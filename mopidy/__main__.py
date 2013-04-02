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


# Extract any non-GStreamer arguments, and leave the GStreamer arguments for
# processing by GStreamer. This needs to be done before GStreamer is imported,
# so that GStreamer doesn't hijack e.g. ``--help``.
# NOTE This naive fix does not support values like ``bar`` in
# ``--gst-foo bar``. Use equals to pass values, like ``--gst-foo=bar``.

def is_gst_arg(argument):
    return argument.startswith('--gst') or argument == '--help-gst'

gstreamer_args = [arg for arg in sys.argv[1:] if is_gst_arg(arg)]
mopidy_args = [arg for arg in sys.argv[1:] if not is_gst_arg(arg)]
sys.argv[1:] = gstreamer_args


# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


from mopidy import exceptions, settings
from mopidy.audio import Audio
from mopidy.config import default_config, config_schemas
from mopidy.core import Core
from mopidy.utils import (
    config as config_utils, deps, log, path, process,
    settings as settings_utils, versioning)


logger = logging.getLogger('mopidy.main')


def main():
    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    loop = gobject.MainLoop()
    options = parse_options()
    config_overrides = getattr(options, 'overrides', [])

    try:
        # TODO: we need a two stage logging setup as we want logging for
        # extension loading and config loading.
        log.setup_logging(None, options.verbosity_level, options.save_debug_log)
        extensions = load_extensions()
        raw_config = load_config(config_overrides, extensions)
        extensions = filter_enabled_extensions(raw_config, extensions)
        config = validate_config(raw_config, extensions)
        check_old_folders()
        setup_settings(options.interactive)
        audio = setup_audio(config)
        backends = setup_backends(config, extensions, audio)
        core = setup_core(audio, backends)
        setup_frontends(config, extensions, core)
        loop.run()
    except exceptions.SettingsError as ex:
        logger.error(ex.message)
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
        b'--help-gst',
        action='store_true', dest='help_gst',
        help='show GStreamer help options')
    parser.add_option(
        b'-i', '--interactive',
        action='store_true', dest='interactive',
        help='ask interactively for required settings which are missing')
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
        b'--debug-thread',
        action='store_true', dest='debug_thread',
        help='run background thread that dumps tracebacks on SIGUSR1')
    parser.add_option(
        b'-o', b'--option',
        action='append', dest='overrides', type='config_override',
        help='`section/key=value` values to override config options')
    return parser.parse_args(args=mopidy_args)[0]


def show_config_callback(option, opt, value, parser):
    overrides = getattr(parser.values, 'overrides', [])

    extensions = load_extensions()
    raw_config = load_config(overrides, extensions)
    enabled_extensions = filter_enabled_extensions(raw_config, extensions)
    config = validate_config(raw_config, enabled_extensions)

    output = ['# Config for disabled extensions are not shown.']
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
            output.append('[%s]\nenabled = false' % extension.ext_name)

    print '\n\n'.join(output)
    sys.exit(0)


def check_old_folders():
    # TODO: add old settings and pre extension storage locations?
    old_settings_folder = os.path.expanduser('~/.mopidy')

    if not os.path.isdir(old_settings_folder):
        return

    logger.warning(
        'Old settings folder found at %s, settings.py should be moved '
        'to %s, any cache data should be deleted. See release notes for '
        'further instructions.', old_settings_folder, path.SETTINGS_PATH)


def load_extensions():
    extensions = []
    for entry_point in pkg_resources.iter_entry_points('mopidy.ext'):
        logger.debug('Loading entrypoint: %s', entry_point)

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
    logging.info('Found following runnable extensions: %s', ', '.join(names))
    return extensions


def filter_enabled_extensions(raw_config, extensions):
    boolean = config_utils.Boolean()
    filtered_extensions = []

    for extension in extensions:
        # TODO: handle key and value errors.
        enabled = raw_config[extension.ext_name]['enabled']
        if boolean.deserialize(enabled):
            filtered_extensions.append(extension)

    names = (e.ext_name for e in filtered_extensions)
    logging.info('Following extensions will be started: %s', ', '.join(names))
    return filtered_extensions


def load_config(options, extensions):
    parser = configparser.RawConfigParser()

    files = [
        '/etc/mopidy/mopidy.conf',
        '$XDG_CONFIG_DIR/mopidy/mopidy.conf',
    ]
    # TODO Add config file given through `options` to `files`
    # TODO Replace `files` with single file given through `options`
    # TODO expand_path and use xdg when loading.

    sources = ['builtin-defaults'] + files + ['command-line']
    logging.info('Loading config from: %s', ', '.join(sources))

    # Read default core config
    parser.readfp(StringIO.StringIO(default_config))

    # Read default extension config
    for extension in extensions:
        parser.readfp(StringIO.StringIO(extension.get_default_config()))

    # Load config from a series of config files
    for filename in files:
        filename = path.expand_path(filename)
        try:
            filehandle = codecs.open(filename, encoding='utf-8')
            parser.readfp(filehandle)
        except IOError:
            logger.debug('Config file %s not found; skipping', filename)
            continue
        except UnicodeDecodeError:
            logger.error('Config file %s is not UTF-8 encoded', filename)
            process.exit_process()

    raw_config = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    for section, key, value in options or []:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


def validate_config(raw_config, extensions):
    # Collect config schemas to validate against
    sections_and_schemas = config_schemas.items()
    for extension in extensions:
        sections_and_schemas.append(
            (extension.ext_name, extension.get_config_schema()))

    # Get validated config
    config = {}
    errors = {}
    for section_name, schema in sections_and_schemas:
        if section_name not in raw_config:
            logger.error('Config section %s not found', section_name)
            process.exit_process()
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
        process.exit_process()

    return config


def setup_settings(interactive):
    path.get_or_create_folder(path.SETTINGS_PATH)
    path.get_or_create_folder(path.DATA_PATH)
    path.get_or_create_file(path.SETTINGS_FILE)
    try:
        settings.validate(interactive)
    except exceptions.SettingsError as ex:
        logger.error(ex.message)
        sys.exit(1)


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
