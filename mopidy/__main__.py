import logging
import signal
import sys

import pykka.debug

from mopidy import commands
from mopidy import config as config_lib
from mopidy import ext
from mopidy.internal import log, path, process, versioning
from mopidy.internal.gi import Gst  # noqa: F401

try:
    # Make GLib's mainloop the event loop for python-dbus
    import dbus.mainloop.glib

    dbus.mainloop.glib.threads_init()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
except ImportError:
    pass


logger = logging.getLogger(__name__)


def main():
    log.bootstrap_delayed_logging()
    logger.info(f"Starting Mopidy {versioning.get_version()}")

    signal.signal(signal.SIGTERM, process.sigterm_handler)
    # Windows does not have signal.SIGUSR1
    if hasattr(signal, "SIGUSR1"):
        signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)

    try:
        registry = ext.Registry()

        root_cmd = commands.RootCommand()
        config_cmd = commands.ConfigCommand()
        deps_cmd = commands.DepsCommand()

        root_cmd.set(extension=None, registry=registry)
        root_cmd.add_child("config", config_cmd)
        root_cmd.add_child("deps", deps_cmd)

        extensions_data = ext.load_extensions()

        for data in extensions_data:
            if data.command:  # TODO: check isinstance?
                data.command.set(extension=data.extension)
                root_cmd.add_child(data.extension.ext_name, data.command)

        args = root_cmd.parse(sys.argv[1:])

        config, config_errors = config_lib.load(
            args.config_files,
            [d.config_schema for d in extensions_data],
            [d.config_defaults for d in extensions_data],
            args.config_overrides,
        )

        create_core_dirs(config)
        create_initial_config_file(args, extensions_data)

        log.setup_logging(
            config, args.base_verbosity_level, args.verbosity_level
        )

        extensions = {
            "validate": [],
            "config": [],
            "disabled": [],
            "enabled": [],
        }
        for data in extensions_data:
            extension = data.extension

            # TODO: factor out all of this to a helper that can be tested
            if not ext.validate_extension_data(data):
                config[extension.ext_name] = {"enabled": False}
                config_errors[extension.ext_name] = {
                    "enabled": "extension disabled by self check."
                }
                extensions["validate"].append(extension)
            elif not config[extension.ext_name]["enabled"]:
                config[extension.ext_name] = {"enabled": False}
                config_errors[extension.ext_name] = {
                    "enabled": "extension disabled by user config."
                }
                extensions["disabled"].append(extension)
            elif config_errors.get(extension.ext_name):
                config[extension.ext_name]["enabled"] = False
                config_errors[extension.ext_name][
                    "enabled"
                ] = "extension disabled due to config errors."
                extensions["config"].append(extension)
            else:
                extensions["enabled"].append(extension)

        log_extension_info(
            [d.extension for d in extensions_data], extensions["enabled"]
        )

        # Config and deps commands are simply special cased for now.
        if args.command == config_cmd:
            schemas = [d.config_schema for d in extensions_data]
            return args.command.run(config, config_errors, schemas)
        elif args.command == deps_cmd:
            return args.command.run()

        check_config_errors(config, config_errors, extensions)

        if not extensions["enabled"]:
            logger.error("No extension enabled, exiting...")
            sys.exit(1)

        # Read-only config from here on, please.
        proxied_config = config_lib.Proxy(config)

        if args.extension and args.extension not in extensions["enabled"]:
            logger.error(
                "Unable to run command provided by disabled extension %s",
                args.extension.ext_name,
            )
            return 1

        for extension in extensions["enabled"]:
            try:
                extension.setup(registry)
            except Exception:
                # TODO: would be nice a transactional registry. But sadly this
                # is a bit tricky since our current API is giving out a mutable
                # list. We might however be able to replace this with a
                # collections.Sequence to provide a RO view.
                logger.exception(
                    f"Extension {extension.ext_name} failed during setup. "
                    f"This might have left the registry in a bad state."
                )

        # Anything that wants to exit after this point must use
        # mopidy.internal.process.exit_process as actors can have been started.
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


def create_core_dirs(config):
    path.get_or_create_dir(config["core"]["cache_dir"])
    path.get_or_create_dir(config["core"]["config_dir"])
    path.get_or_create_dir(config["core"]["data_dir"])


def create_initial_config_file(args, extensions_data):
    """Initialize whatever the last config file is with defaults"""

    config_file = path.expand_path(args.config_files[-1])

    if config_file.exists():
        return

    try:
        default = config_lib.format_initial(extensions_data)
        path.get_or_create_file(
            config_file,
            mkdir=False,
            content=default.encode(errors="surrogateescape"),
        )
        logger.info(f"Initialized {config_file.as_uri()} with default config")
    except OSError as exc:
        logger.warning(
            f"Unable to initialize {config_file.as_uri()} with default config: {exc}"
        )


def log_extension_info(all_extensions, enabled_extensions):
    # TODO: distinguish disabled vs blocked by env?
    enabled_names = {e.ext_name for e in enabled_extensions}
    disabled_names = {e.ext_name for e in all_extensions} - enabled_names
    logger.info("Enabled extensions: %s", ", ".join(enabled_names) or "none")
    logger.info("Disabled extensions: %s", ", ".join(disabled_names) or "none")


def check_config_errors(config, errors, extensions):
    fatal_errors = []
    extension_names = {}
    all_extension_names = set()

    for state in extensions:
        extension_names[state] = {e.ext_name for e in extensions[state]}
        all_extension_names.update(extension_names[state])

    for section in sorted(errors):
        if not errors[section]:
            continue

        if section not in all_extension_names:
            logger.warning(f"Found fatal {section} configuration errors:")
            fatal_errors.append(section)
        elif section in extension_names["config"]:
            del errors[section]["enabled"]
            logger.warning(
                f"Found {section} configuration errors. "
                f"The extension has been automatically disabled:"
            )
        else:
            continue

        for field, msg in errors[section].items():
            logger.warning(f"  {section}/{field} {msg}")

    if extensions["config"]:
        logger.warning(
            "Please fix the extension configuration errors or "
            "disable the extensions to silence these messages."
        )

    if fatal_errors:
        logger.error("Please fix fatal configuration errors, exiting...")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
