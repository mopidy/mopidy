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
from mopidy.utils import deps, log, path, process, versioning

logger = logging.getLogger('mopidy.main')


def main():
    log.bootstrap_delayed_logging()
    logger.info('Starting Mopidy %s', versioning.get_version())

    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    try:
        create_file_structures()
        check_old_locations()

        parser, subparser = commands.build_parser()
        installed_extensions = ext.load_extensions()
        extension_sub_commands = {}

        for extension in installed_extensions:
            for cls in extension.get_sub_commands():
                cmd_parser = subparser.add_parser(bytes(cls.name),
                                                  help=cls.help)
                extension_sub_commands[cls.name] = (extension, cls(cmd_parser))

        args = parser.parse_args(args=mopidy_args)
        if args.command in ('deps', 'config'):
            args.verbosity_level -= 1

        config, config_errors = config_lib.load(
            args.config_files, installed_extensions, args.config_overrides)

        log.setup_logging(config, args.verbosity_level, args.save_debug_log)

        enabled_extensions = []
        for extension in installed_extensions:
            if not ext.validate_extension(extension):
                config[extension.ext_name] = {'enabled': False}
                config_errors[extension.ext_name] = {
                    'enabled': 'extension disabled by self check.'}
            elif not config[extension.ext_name]['enabled']:
                config[extension.ext_name] = {'enabled': False}
                config_errors[extension.ext_name] = {
                    'enabled': 'extension disabled by user config.'}
            else:
                enabled_extensions.append(extension)

        log_extension_info(installed_extensions, enabled_extensions)

        if args.command == 'config':
            logger.info('Dumping sanitized user config and exiting.')
            print config_lib.format(
                config, installed_extensions, config_errors)
            sys.exit(0)
        elif args.command == 'deps':
            logger.info('Dumping debug info about dependencies and exiting.')
            print deps.format_dependency_list()
            sys.exit(0)

        # Remove errors for extensions that are not enabled:
        for extension in installed_extensions:
            if extension not in enabled_extensions:
                config_errors.pop(extension.ext_name, None)

        check_config_errors(config_errors)

        # Read-only config from here on, please.
        proxied_config = config_lib.Proxy(config)

        if args.command in extension_sub_commands:
            extension, cmd = extension_sub_commands[args.command]

            if extension not in enabled_extensions:
                parser.error('Can not run sub-command %s from the disabled '
                             'extension %s.' % (cmd.name, extension.ext_name))

            logging.info('Running %s command provided by %s.', cmd.name,
                         extension.ext_name)
            sys.exit(cmd.run(args, proxied_config, enabled_extensions))

        if args.command == 'run':
            ext.register_gstreamer_elements(enabled_extensions)

            # Anything that wants to exit after this point must use
            # mopidy.utils.process.exit_process as actors have been started.
            start(proxied_config, enabled_extensions)
            sys.exit(0)

        parser.error(
            'Unknown command %s, this should never happen.' % args.command)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logger.exception(ex)
        raise


def bootstrap_logging(args):
    # Initial config without extensions to bootstrap logging.
    logging_config, _ = config_lib.load(
        args.config_files, [], args.config_overrides)

    # TODO: setup_logging needs defaults in-case config values are None
    log.setup_logging(
        logging_config, args.verbosity_level, args.save_debug_log)


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
