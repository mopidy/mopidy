from __future__ import unicode_literals

import logging
import os
import signal
import sys

import gobject
gobject.threads_init()

import pykka.debug


# Extract any command line arguments. This needs to be done before GStreamer is
# imported, so that GStreamer doesn't hijack e.g. ``--help``.
mopidy_args = sys.argv[1:]
sys.argv[1:] = []


from mopidy import commands, ext
from mopidy.audio import Audio
from mopidy import config as config_lib
from mopidy.core import Core
from mopidy.utils import log, path, process

logger = logging.getLogger('mopidy.main')


def main():
    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    args = commands.parser.parse_args(args=mopidy_args)
    if args.show_config:
        commands.show_config(args)
    if args.show_deps:
        commands.show_deps()

    # TODO: figure out a way to make the boilerplate in this file reusable in
    # scanner and other places we need it.

    try:
        # Initial config without extensions to bootstrap logging.
        logging_initialized = False
        logging_config, _ = config_lib.load(
            args.config_files, [], args.config_overrides)

        # TODO: setup_logging needs defaults in-case config values are None
        log.setup_logging(
            logging_config, args.verbosity_level, args.save_debug_log)
        logging_initialized = True

        create_file_structures()
        check_old_locations()

        installed_extensions = ext.load_extensions()

        config, config_errors = config_lib.load(
            args.config_files, installed_extensions, args.config_overrides)

        # Filter out disabled extensions and remove any config errors for them.
        enabled_extensions = []
        for extension in installed_extensions:
            enabled = config[extension.ext_name]['enabled']
            if ext.validate_extension(extension) and enabled:
                enabled_extensions.append(extension)
            elif extension.ext_name in config_errors:
                del config_errors[extension.ext_name]

        log_extension_info(installed_extensions, enabled_extensions)
        check_config_errors(config_errors)

        # Read-only config from here on, please.
        proxied_config = config_lib.Proxy(config)

        log.setup_log_levels(proxied_config)
        ext.register_gstreamer_elements(enabled_extensions)

        # Anything that wants to exit after this point must use
        # mopidy.utils.process.exit_process as actors have been started.
        start(proxied_config, enabled_extensions)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        if logging_initialized:
            logger.exception(ex)
        raise


def create_file_structures():
    path.get_or_create_dir(b'$XDG_DATA_DIR/mopidy')
    path.get_or_create_file(b'$XDG_CONFIG_DIR/mopidy/mopidy.conf')


def check_old_locations():
    dot_mopidy_dir = path.expand_path(b'~/.mopidy')
    if os.path.isdir(dot_mopidy_dir):
        logger.warning(
            'Old Mopidy dot dir found at %s. Please migrate your config to '
            'the ini-file based config format. See release notes for further '
            'instructions.', dot_mopidy_dir)

    old_settings_file = path.expand_path(b'$XDG_CONFIG_DIR/mopidy/settings.py')
    if os.path.isfile(old_settings_file):
        logger.warning(
            'Old Mopidy settings file found at %s. Please migrate your '
            'config to the ini-file based config format. See release notes '
            'for further instructions.', old_settings_file)


def log_extension_info(all_extensions, enabled_extensions):
    # TODO: distinguish disabled vs blocked by env?
    enabled_names = set(e.ext_name for e in enabled_extensions)
    disabled_names = set(e.ext_name for e in all_extensions) - enabled_names
    logging.info(
        'Enabled extensions: %s', ', '.join(enabled_names) or 'none')
    logging.info(
        'Disabled extensions: %s', ', '.join(disabled_names) or 'none')


def check_config_errors(errors):
    if not errors:
        return
    for section in errors:
        for key, msg in errors[section].items():
            logger.error('Config value %s/%s %s', section, key, msg)
    sys.exit(1)


def start(config, extensions):
    loop = gobject.MainLoop()
    try:
        audio = start_audio(config)
        backends = start_backends(config, extensions, audio)
        core = start_core(audio, backends)
        start_frontends(config, extensions, core)
        loop.run()
    except KeyboardInterrupt:
        logger.info('Interrupted. Exiting...')
        return
    finally:
        loop.quit()
        stop_frontends(extensions)
        stop_core()
        stop_backends(extensions)
        stop_audio()
        process.stop_remaining_actors()


def start_audio(config):
    logger.info('Starting Mopidy audio')
    return Audio.start(config=config).proxy()


def stop_audio():
    logger.info('Stopping Mopidy audio')
    process.stop_actors_by_class(Audio)


def start_backends(config, extensions, audio):
    backend_classes = []
    for extension in extensions:
        backend_classes.extend(extension.get_backend_classes())

    logger.info(
        'Starting Mopidy backends: %s',
        ', '.join(b.__name__ for b in backend_classes) or 'none')

    backends = []
    for backend_class in backend_classes:
        backend = backend_class.start(config=config, audio=audio).proxy()
        backends.append(backend)

    return backends


def stop_backends(extensions):
    logger.info('Stopping Mopidy backends')
    for extension in extensions:
        for backend_class in extension.get_backend_classes():
            process.stop_actors_by_class(backend_class)


def start_core(audio, backends):
    logger.info('Starting Mopidy core')
    return Core.start(audio=audio, backends=backends).proxy()


def stop_core():
    logger.info('Stopping Mopidy core')
    process.stop_actors_by_class(Core)


def start_frontends(config, extensions, core):
    frontend_classes = []
    for extension in extensions:
        frontend_classes.extend(extension.get_frontend_classes())

    logger.info(
        'Starting Mopidy frontends: %s',
        ', '.join(f.__name__ for f in frontend_classes) or 'none')

    for frontend_class in frontend_classes:
        frontend_class.start(config=config, core=core)


def stop_frontends(extensions):
    logger.info('Stopping Mopidy frontends')
    for extension in extensions:
        for frontend_class in extension.get_frontend_classes():
            process.stop_actors_by_class(frontend_class)


if __name__ == '__main__':
    main()
