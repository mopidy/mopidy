from __future__ import unicode_literals

import logging
import os
import signal
import sys

import gobject
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


from mopidy import commands, ext
from mopidy import config as config_lib
from mopidy.utils import log, path, process, versioning

logger = logging.getLogger('mopidy.main')


def main():
    log.bootstrap_delayed_logging()
    logger.info('Starting Mopidy %s', versioning.get_version())

    signal.signal(signal.SIGTERM, process.exit_handler)
    signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    try:
        root_cmd = commands.RootCommand()
        config_cmd = commands.ConfigCommand()
        deps_cmd = commands.DepsCommand()

        root_cmd.set(extension=None)
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
        ext.register_gstreamer_elements(enabled_extensions)

        # Config and deps commands are simply special cased for now.
        if args.command == config_cmd:
            return args.command.run(
                config, config_errors, installed_extensions)
        elif args.command == deps_cmd:
            return args.command.run()

        # Remove errors for extensions that are not enabled:
        for extension in installed_extensions:
            if extension not in enabled_extensions:
                config_errors.pop(extension.ext_name, None)
        check_config_errors(config_errors)

        # Read-only config from here on, please.
        proxied_config = config_lib.Proxy(config)

        if args.extension and args.extension not in enabled_extensions:
            logger.error(
                'Unable to run command provided by disabled extension %s',
                args.extension.ext_name)
            return 1

        # Anything that wants to exit after this point must use
        # mopidy.utils.process.exit_process as actors can have been started.
        try:
            return args.command.run(args, proxied_config, enabled_extensions)
        except NotImplementedError:
            print root_cmd.format_help()
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
    if os.path.exists(config_file):
        return

    try:
        default = config_lib.format_initial(extensions)
        path.get_or_create_file(config_file, mkdir=False, content=default)
        logger.info('Initialized %s with default config', config_file)
    except IOError as e:
        logger.warning('Unable to initialize %s with default config: %s',
                       config_file, e)


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


if __name__ == '__main__':
    sys.exit(main())
