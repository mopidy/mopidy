from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import signal
import sys
import textwrap

try:
    import gobject   # noqa
except ImportError:
    print(textwrap.dedent("""
        ERROR: The gobject Python package was not found.

        Mopidy requires GStreamer (and GObject) to work. These are C libraries
        with a number of dependencies themselves, and cannot be installed with
        the regular Python tools like pip.

        Please see http://docs.mopidy.com/en/latest/installation/ for
        instructions on how to install the required dependencies.
    """))
    raise

gobject.threads_init()

try:
    # Make GObject's mainloop the event loop for python-dbus
    import dbus.mainloop.glib
    dbus.mainloop.glib.threads_init()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
except ImportError:
    pass

import pykka.debug


# Extract any command line arguments. This needs to be done before GStreamer is
# imported, so that GStreamer doesn't hijack e.g. ``--help``.
mopidy_args = sys.argv[1:]
sys.argv[1:] = []


from mopidy import commands, config as config_lib, ext
from mopidy.utils import encoding, log, path, process, versioning

logger = logging.getLogger(__name__)


def main():
    log.bootstrap_delayed_logging()
    logger.info('Starting Mopidy %s', versioning.get_version())

    signal.signal(signal.SIGTERM, process.exit_handler)
    # Windows does not have signal.SIGUSR1
    if hasattr(signal, 'SIGUSR1'):
        signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    try:
        registry = ext.Registry()

        root_cmd = commands.RootCommand()
        config_cmd = commands.ConfigCommand()
        deps_cmd = commands.DepsCommand()

        root_cmd.set(extension=None, registry=registry)
        root_cmd.add_child('config', config_cmd)
        root_cmd.add_child('deps', deps_cmd)

        installed_extensions = ext.load_extensions()

        for extension in installed_extensions:
            ext_cmd = extension.get_command()
            if ext_cmd:
                ext_cmd.set(extension=extension)
                root_cmd.add_child(extension.ext_name, ext_cmd)

        args = root_cmd.parse(mopidy_args)

        create_file_structures_and_config(args, installed_extensions)
        check_old_locations()

        config, config_errors = config_lib.load(
            args.config_files, installed_extensions, args.config_overrides)

        verbosity_level = args.base_verbosity_level
        if args.verbosity_level:
            verbosity_level += args.verbosity_level

        log.setup_logging(config, verbosity_level, args.save_debug_log)

        extensions = {
            'validate': [], 'config': [], 'disabled': [], 'enabled': []}
        for extension in installed_extensions:
            if not ext.validate_extension(extension):
                config[extension.ext_name] = {'enabled': False}
                config_errors[extension.ext_name] = {
                    'enabled': 'extension disabled by self check.'}
                extensions['validate'].append(extension)
            elif not config[extension.ext_name]['enabled']:
                config[extension.ext_name] = {'enabled': False}
                config_errors[extension.ext_name] = {
                    'enabled': 'extension disabled by user config.'}
                extensions['disabled'].append(extension)
            elif config_errors.get(extension.ext_name):
                config[extension.ext_name]['enabled'] = False
                config_errors[extension.ext_name]['enabled'] = (
                    'extension disabled due to config errors.')
                extensions['config'].append(extension)
            else:
                extensions['enabled'].append(extension)

        log_extension_info(installed_extensions, extensions['enabled'])

        # Config and deps commands are simply special cased for now.
        if args.command == config_cmd:
            return args.command.run(
                config, config_errors, installed_extensions)
        elif args.command == deps_cmd:
            return args.command.run()

        check_config_errors(config, config_errors, extensions)

        if not extensions['enabled']:
            logger.error('No extension enabled, exiting...')
            sys.exit(1)

        # Read-only config from here on, please.
        proxied_config = config_lib.Proxy(config)

        if args.extension and args.extension not in extensions['enabled']:
            logger.error(
                'Unable to run command provided by disabled extension %s',
                args.extension.ext_name)
            return 1

        for extension in extensions['enabled']:
            extension.setup(registry)

        # Anything that wants to exit after this point must use
        # mopidy.utils.process.exit_process as actors can have been started.
        try:
            return args.command.run(args, proxied_config)
        except NotImplementedError:
            print(root_cmd.format_help())
            return 1

    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logger.exception(ex)
        raise


def create_file_structures_and_config(args, extensions):
    path.get_or_create_dir(b'$XDG_DATA_DIR/mopidy')
    path.get_or_create_dir(b'$XDG_CONFIG_DIR/mopidy')

    # Initialize whatever the last config file is with defaults
    config_file = args.config_files[-1]
    if os.path.exists(path.expand_path(config_file)):
        return

    try:
        default = config_lib.format_initial(extensions)
        path.get_or_create_file(config_file, mkdir=False, content=default)
        logger.info('Initialized %s with default config', config_file)
    except IOError as error:
        logger.warning(
            'Unable to initialize %s with default config: %s',
            config_file, encoding.locale_decode(error))


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
    logger.info(
        'Enabled extensions: %s', ', '.join(enabled_names) or 'none')
    logger.info(
        'Disabled extensions: %s', ', '.join(disabled_names) or 'none')


def check_config_errors(config, errors, extensions):
    fatal_errors = []
    extension_names = {}
    all_extension_names = set()

    for state in extensions:
        extension_names[state] = set(e.ext_name for e in extensions[state])
        all_extension_names.update(extension_names[state])

    for section in sorted(errors):
        if not errors[section]:
            continue

        if section not in all_extension_names:
            logger.warning('Found fatal %s configuration errors:', section)
            fatal_errors.append(section)
        elif section in extension_names['config']:
            del errors[section]['enabled']
            logger.warning('Found %s configuration errors, the extension '
                           'has been automatically disabled:', section)
        else:
            continue

        for field, msg in errors[section].items():
            logger.warning('  %s/%s %s', section, field, msg)

    if extensions['config']:
        logger.warning('Please fix the extension configuration errors or '
                       'disable the extensions to silence these messages.')

    if fatal_errors:
        logger.error('Please fix fatal configuration errors, exiting...')
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
