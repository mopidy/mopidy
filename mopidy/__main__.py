from __future__ import unicode_literals

import logging
import optparse
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


# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


from mopidy import ext
from mopidy.audio import Audio
from mopidy import config as config_lib
from mopidy.core import Core
from mopidy.utils import deps, log, path, process, versioning

logger = logging.getLogger('mopidy.main')


def main():
    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    loop = gobject.MainLoop()
    options = parse_options()
    config_files = options.config.split(':')
    config_overrides = options.overrides

    extensions = []  # Make sure it is defined before the finally block

    # TODO: figure out a way to make the boilerplate in this file reusable in
    # scanner and other places we need it.

    try:
        create_file_structures()
        # TODO: run raw logging config trough escape code etc, or just validate?
        logging_config = config_lib.load(config_files, config_overrides)
        log.setup_logging(
            logging_config, options.verbosity_level, options.save_debug_log)
        installed_extensions = ext.load_extensions()
        extensions = ext.validate_extensions(installed_extensions)
        raw_config = config_lib.load(config_files, config_overrides, extensions)
        extensions = ext.filter_enabled_extensions(raw_config, extensions)
        config = config_lib.validate(
            raw_config, config_lib.core_schemas, extensions)
        log.setup_log_levels(config)
        check_old_locations()

        # TODO: wrap config in RO proxy.

        # Anything that wants to exit after this point must use
        # mopidy.utils.process.exit_process as actors have been started.
        audio = setup_audio(config)
        backends = setup_backends(config, extensions, audio)
        core = setup_core(audio, backends)
        setup_frontends(config, extensions, core)
        loop.run()
    except KeyboardInterrupt:
        logger.info('Interrupted. Exiting...')
    except Exception as ex:
        logger.exception(ex)
    finally:
        loop.quit()
        stop_frontends(extensions)
        stop_core()
        stop_backends(extensions)
        stop_audio()
        process.stop_remaining_actors()


def check_config_override(option, opt, override):
    try:
        return config_lib.parse_override(override)
    except ValueError:
        raise optparse.OptionValueError(
            'option %s: must have the format section/key=value' % opt)


def parse_options():
    parser = optparse.OptionParser(
        version='Mopidy %s' % versioning.get_version())

    # Ugly extension of optparse type checking magic :/
    optparse.Option.TYPES += ('config_override',)
    optparse.Option.TYPE_CHECKER['config_override'] = check_config_override

    # NOTE First argument to add_option must be bytestrings on Python < 2.6.2
    # See https://github.com/mopidy/mopidy/issues/302 for details
    parser.add_option(
        b'-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option(
        b'-v', '--verbose',
        action='count', default=1, dest='verbosity_level',
        help='more output (debug level)')
    parser.add_option(
        b'--save-debug-log',
        action='store_true', dest='save_debug_log',
        help='save debug log to "./mopidy.log"')
    parser.add_option(
        b'--show-config',
        action='callback', callback=show_config_callback,
        help='show current config')
    parser.add_option(
        b'--list-deps',
        action='callback', callback=deps.list_deps_optparse_callback,
        help='list dependencies and their versions')
    parser.add_option(
        b'--config',
        action='store', dest='config',
        default='/etc/mopidy/mopidy.conf:$XDG_CONFIG_DIR/mopidy/mopidy.conf',
        help='config files to use, colon seperated, later files override')
    parser.add_option(
        b'-o', b'--option',
        action='append', dest='overrides', type='config_override',
        help='`section/key=value` values to override config options')
    return parser.parse_args(args=mopidy_args)[0]


def show_config_callback(option, opt, value, parser):
    # TODO: don't use callback for this as --config or -o set after
    # --show-config will be ignored.
    files = getattr(parser.values, 'config', '').split(':')
    overrides = getattr(parser.values, 'overrides', [])

    extensions = ext.load_extensions()
    raw_config = config_lib.load(files, overrides, extensions)
    enabled_extensions = ext.filter_enabled_extensions(raw_config, extensions)
    config = config_lib.validate(
        raw_config, config_lib.core_schemas, enabled_extensions)

    # TODO: create mopidy.config.format?
    output = []
    for schema in config_lib.core_schemas:
        options = config.get(schema.name, {})
        if not options:
            continue
        output.append(schema.format(options))

    for extension in extensions:
        schema = extension.get_config_schema()

        if extension in enabled_extensions:
            options = config.get(schema.name, {})
            output.append(schema.format(options))
        else:
            lines = ['[%s]' % schema.name, 'enabled = false',
                     '# Config hidden as extension is disabled']
            output.append('\n'.join(lines))

    print '\n\n'.join(output)
    sys.exit(0)


def check_old_locations():
    dot_mopidy_dir = path.expand_path('~/.mopidy')
    if os.path.isdir(dot_mopidy_dir):
        logger.warning(
            'Old Mopidy dot dir found at %s. Please migrate your config to '
            'the ini-file based config format. See release notes for further '
            'instructions.', dot_mopidy_dir)

    old_settings_file = path.expand_path('$XDG_CONFIG_DIR/mopidy/settings.py')
    if os.path.isfile(old_settings_file):
        logger.warning(
            'Old Mopidy settings file found at %s. Please migrate your '
            'config to the ini-file based config format. See release notes '
            'for further instructions.', old_settings_file)


def create_file_structures():
    path.get_or_create_dir('$XDG_DATA_DIR/mopidy')
    path.get_or_create_file('$XDG_CONFIG_DIR/mopidy/mopidy.conf')


def setup_audio(config):
    logger.info('Starting Mopidy audio')
    return Audio.start(config=config).proxy()


def stop_audio():
    logger.info('Stopping Mopidy audio')
    process.stop_actors_by_class(Audio)


def setup_backends(config, extensions, audio):
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


def setup_core(audio, backends):
    logger.info('Starting Mopidy core')
    return Core.start(audio=audio, backends=backends).proxy()


def stop_core():
    logger.info('Stopping Mopidy core')
    process.stop_actors_by_class(Core)


def setup_frontends(config, extensions, core):
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
