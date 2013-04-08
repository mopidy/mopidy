from __future__ import unicode_literals

import codecs
import ConfigParser as configparser
import logging
import optparse
import os
import signal
import StringIO
import sys

import gobject
gobject.threads_init()

import pkg_resources
import pykka.debug


# Extract any command line arguments. This needs to be done before GStreamer is
# imported, so that GStreamer doesn't hijack e.g. ``--help``.
mopidy_args = sys.argv[1:]
sys.argv[1:] = []


# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


from mopidy import exceptions
from mopidy.audio import Audio
from mopidy.config import default_config, config_schemas
from mopidy.core import Core
from mopidy.utils import (
    config as config_utils, deps, log, path, process, versioning)


logger = logging.getLogger('mopidy.main')


def main():
    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    loop = gobject.MainLoop()
    options = parse_options()
    config_files = options.config.split(':')
    config_overrides = options.overrides

    extensions = []  # Make sure it is defined before the finally block

    try:
        create_file_structures()
        logging_config = load_config(config_files, config_overrides)
        log.setup_logging(
            logging_config, options.verbosity_level, options.save_debug_log)
        extensions = load_extensions()
        raw_config = load_config(config_files, config_overrides, extensions)
        extensions = filter_enabled_extensions(raw_config, extensions)
        config = validate_config(raw_config, config_schemas, extensions)
        log.setup_log_levels(config)
        check_old_locations()

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
        section, remainder = override.split('/', 1)
        key, value = remainder.split('=', 1)
        return (section, key, value)
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

    extensions = load_extensions()
    raw_config = load_config(files, overrides, extensions)
    enabled_extensions = filter_enabled_extensions(raw_config, extensions)
    config = validate_config(raw_config, config_schemas, enabled_extensions)

    output = []
    for section_name, schema in config_schemas.items():
        options = config.get(section_name, {})
        if not options:
            continue
        output.append(schema.format(section_name, options))

    for extension in extensions:
        if extension in enabled_extensions:
            schema = extension.get_config_schema()
            options = config.get(extension.ext_name, {})
            output.append(schema.format(extension.ext_name, options))
        else:
            lines = ['[%s]' % extension.ext_name, 'enabled = false',
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


def load_extensions():
    extensions = []
    for entry_point in pkg_resources.iter_entry_points('mopidy.ext'):
        logger.debug('Loading entry point: %s', entry_point)

        try:
            extension_class = entry_point.load()
        except pkg_resources.DistributionNotFound as ex:
            logger.info(
                'Disabled extension %s: Dependency %s not found',
                entry_point.name, ex)
            continue

        extension = extension_class()

        logger.debug(
            'Loaded extension: %s %s', extension.dist_name, extension.version)

        if entry_point.name != extension.ext_name:
            logger.warning(
                'Disabled extension %(ep)s: entry point name (%(ep)s) '
                'does not match extension name (%(ext)s)',
                {'ep': entry_point.name, 'ext': extension.ext_name})
            continue

        try:
            extension.validate_environment()
        except exceptions.ExtensionError as ex:
            logger.info(
                'Disabled extension %s: %s', entry_point.name, ex.message)
            continue

        extensions.append(extension)

    names = (e.ext_name for e in extensions)
    logging.debug('Discovered extensions: %s', ', '.join(names))
    return extensions


def filter_enabled_extensions(raw_config, extensions):
    boolean = config_utils.Boolean()
    enabled_extensions = []
    enabled_names = []
    disabled_names = []

    for extension in extensions:
        # TODO: handle key and value errors.
        enabled = raw_config[extension.ext_name]['enabled']
        if boolean.deserialize(enabled):
            enabled_extensions.append(extension)
            enabled_names.append(extension.ext_name)
        else:
            disabled_names.append(extension.ext_name)

    logging.info('Enabled extensions: %s', ', '.join(enabled_names))
    logging.info('Disabled extensions: %s', ', '.join(disabled_names))
    return enabled_extensions


def load_config(files, overrides, extensions=None):
    parser = configparser.RawConfigParser()

    files = [path.expand_path(f) for f in files]
    sources = ['builtin-defaults'] + files + ['command-line']
    logger.info('Loading config from: %s', ', '.join(sources))

    # Read default core config
    parser.readfp(StringIO.StringIO(default_config))

    # Read default extension config
    for extension in extensions or []:
        parser.readfp(StringIO.StringIO(extension.get_default_config()))

    # Load config from a series of config files
    for filename in files:
        # TODO: if this is the initial load of logging config we might not have
        # a logger at this point, we might want to handle this better.
        try:
            filehandle = codecs.open(filename, encoding='utf-8')
            parser.readfp(filehandle)
        except IOError:
            logger.debug('Config file %s not found; skipping', filename)
            continue
        except UnicodeDecodeError:
            logger.error('Config file %s is not UTF-8 encoded', filename)
            sys.exit(1)

    raw_config = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    for section, key, value in overrides or []:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


def validate_config(raw_config, schemas, extensions=None):
    # Collect config schemas to validate against
    sections_and_schemas = schemas.items()
    for extension in extensions or []:
        sections_and_schemas.append(
            (extension.ext_name, extension.get_config_schema()))

    # Get validated config
    config = {}
    errors = {}
    for section_name, schema in sections_and_schemas:
        if section_name not in raw_config:
            errors[section_name] = {section_name: 'section not found'}
        try:
            items = raw_config[section_name].items()
            config[section_name] = schema.convert(items)
        except exceptions.ConfigError as error:
            errors[section_name] = error

    if errors:
        for section_name, error in errors.items():
            logger.error('[%s] config errors:', section_name)
            for key in error:
                logger.error('%s %s', key, error[key])
        sys.exit(1)

    return config


def create_file_structures():
    path.get_or_create_dir('$XDG_DATA_DIR/mopidy')
    path.get_or_create_dir('$XDG_CONFIG_DIR/mopidy')
    path.get_or_create_file('$XDG_CONFIG_DIR/mopidy/mopidy.conf')


def setup_audio(config):
    logger.info('Starting Mopidy audio')
    return Audio.start(config=config).proxy()


def stop_audio():
    logger.info('Stopping Mopidy audio')
    process.stop_actors_by_class(Audio)


def setup_backends(config, extensions, audio):
    logger.info('Starting Mopidy backends')
    backends = []
    for extension in extensions:
        for backend_class in extension.get_backend_classes():
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
    logger.info('Starting Mopidy frontends')
    for extension in extensions:
        for frontend_class in extension.get_frontend_classes():
            frontend_class.start(config=config, core=core)


def stop_frontends(extensions):
    logger.info('Stopping Mopidy frontends')
    for extension in extensions:
        for frontend_class in extension.get_frontend_classes():
            process.stop_actors_by_class(frontend_class)


if __name__ == '__main__':
    main()
