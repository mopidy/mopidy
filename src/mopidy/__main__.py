from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

import pykka.debug

import mopidy
from mopidy import commands, ext
from mopidy import config as config_lib
from mopidy.internal import log, path, process
from mopidy.internal.gi import (
    GLib,
    Gst,  # noqa: F401 (imported to test GStreamer presence)
)

try:
    # Make GLib's mainloop the event loop for python-dbus
    import dbus.mainloop.glib  # pyright: ignore[reportMissingImports]

    dbus.mainloop.glib.threads_init()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
except ImportError:
    pass

if TYPE_CHECKING:

    class ExtensionsStatus(TypedDict):
        validate: list[ext.Extension]
        config: list[ext.Extension]
        disabled: list[ext.Extension]
        enabled: list[ext.Extension]


logger = logging.getLogger(__name__)


def main() -> int:  # noqa: C901, PLR0912, PLR0915
    log.bootstrap_delayed_logging()
    logger.info(f"Starting Mopidy {mopidy.__version__}")

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

        default_config_files = [
            (Path(base) / "mopidy" / "mopidy.conf").resolve()
            for base in [*GLib.get_system_config_dirs(), GLib.get_user_config_dir()]
        ]
        config_files = [
            Path(f) for f in args.config_files or []
        ] or default_config_files

        config, config_errors = config_lib.load(
            config_files,
            [d.config_schema for d in extensions_data],
            [d.config_defaults for d in extensions_data],
            args.config_overrides,
        )

        create_core_dirs(config)
        create_initial_config_file(config_files, extensions_data)

        log.setup_logging(config, args.base_verbosity_level, args.verbosity_level)

        extensions_status: ExtensionsStatus = {
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
                    "enabled": "extension disabled by self check.",
                }
                extensions_status["validate"].append(extension)
            elif not config[extension.ext_name]["enabled"]:
                config[extension.ext_name] = {"enabled": False}
                config_errors[extension.ext_name] = {
                    "enabled": "extension disabled by user config.",
                }
                extensions_status["disabled"].append(extension)
            elif config_errors.get(extension.ext_name):
                config[extension.ext_name]["enabled"] = False
                config_errors[extension.ext_name]["enabled"] = (
                    "extension disabled due to config errors."
                )
                extensions_status["config"].append(extension)
            else:
                extensions_status["enabled"].append(extension)

        log_extension_info(
            [d.extension for d in extensions_data],
            extensions_status["enabled"],
        )

        # Config and deps commands are simply special cased for now.
        if isinstance(args.command, commands.ConfigCommand):
            return args.command.run(
                args=args,
                config=config,
                errors=config_errors,
                schemas=[d.config_schema for d in extensions_data],
            )
        if isinstance(args.command, commands.DepsCommand):
            return args.command.run(
                args=args,
                config=config,
            )

        check_config_errors(config_errors, extensions_status)

        if not extensions_status["enabled"]:
            logger.error("No extension enabled, exiting...")
            sys.exit(1)

        # Read-only config from here on, please.
        proxied_config = cast(config_lib.Config, config_lib.Proxy(config))

        if args.extension and args.extension not in extensions_status["enabled"]:
            logger.error(
                "Unable to run command provided by disabled extension %s",
                args.extension.ext_name,
            )
            return 1

        for extension in extensions_status["enabled"]:
            try:
                extension.setup(registry)
            except Exception:
                # TODO: would be nice a transactional registry. But sadly this
                # is a bit tricky since our current API is giving out a mutable
                # list. We might however be able to replace this with a
                # collections.Sequence to provide a RO view.
                logger.exception(
                    f"Extension {extension.ext_name} failed during setup. "
                    f"This might have left the registry in a bad state.",
                )

        # Anything that wants to exit after this point must use
        # mopidy.internal.process.exit_process as actors can have been started.
        try:
            assert isinstance(args.command, commands.Command)
            return args.command.run(
                args=args,
                config=proxied_config,
            )
        except NotImplementedError:
            print(root_cmd.format_help())  # noqa: T201
            return 1

    except KeyboardInterrupt:
        return 0
    except Exception:
        logger.exception("Unhandled exception")
        raise


def create_core_dirs(config):
    path.get_or_create_dir(config["core"]["cache_dir"])
    path.get_or_create_dir(config["core"]["config_dir"])
    path.get_or_create_dir(config["core"]["data_dir"])


def create_initial_config_file(config_files, extensions_data):
    """Initialize whatever the last config file is with defaults."""
    config_file = path.expand_path(config_files[-1])

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
            f"Unable to initialize {config_file.as_uri()} with default config: {exc}",
        )


def log_extension_info(all_extensions, enabled_extensions):
    # TODO: distinguish disabled vs blocked by env?
    enabled_names = {e.ext_name for e in enabled_extensions}
    disabled_names = {e.ext_name for e in all_extensions} - enabled_names
    logger.info("Enabled extensions: %s", ", ".join(enabled_names) or "none")
    logger.info("Disabled extensions: %s", ", ".join(disabled_names) or "none")


def check_config_errors(
    errors: config_lib.ConfigErrors,
    extensions_status: ExtensionsStatus,
) -> None:
    fatal_errors = []
    extension_names = {}
    all_extension_names = set()

    for state in extensions_status:
        extension_names[state] = {e.ext_name for e in extensions_status[state]}
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
                f"The extension has been automatically disabled:",
            )
        else:
            continue

        for field, msg in errors[section].items():
            logger.warning(f"  {section}/{field} {msg}")

    if extensions_status["config"]:
        logger.warning(
            "Please fix the extension configuration errors or "
            "disable the extensions to silence these messages.",
        )

    if fatal_errors:
        logger.error("Please fix fatal configuration errors, exiting...")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
