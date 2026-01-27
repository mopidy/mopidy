from __future__ import annotations

import logging
import os
import sys
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from cyclopts import App, Group, Parameter, Token
from platformdirs import PlatformDirs

import mopidy
from mopidy._app import config, deps, logs, process, server
from mopidy._app.config import ConfigLoader, ConfigManager, ConfigOverrides
from mopidy._app.extensions import ExtensionManager, ExtensionStatus
from mopidy.config import Config

logger = logging.getLogger(__name__)


def early_setup() -> ExtensionManager | None:
    try:
        logs.bootstrap_delayed_logging()
        logger.info(f"Starting Mopidy {mopidy.__version__}")

        # Setup signal handlers so we can always shut down cleanly
        process.setup_signal_handlers()

        # Load extensions
        extensions = ExtensionManager.discover()
        ExtensionManager.set_global(extensions)
    except KeyboardInterrupt:
        return None
    except Exception:
        logger.exception("Unhandled exception")
        raise
    else:
        return extensions


def config_paths_default() -> list[Path]:
    # Use /etc instead of /etc/xdg unless XDG_CONFIG_DIRS is set.
    os.environ.setdefault("XDG_CONFIG_DIRS", "/etc")
    dirs = PlatformDirs(appname="mopidy", appauthor="mopidy")
    return [
        dirs.site_config_path / "mopidy.conf",
        dirs.user_config_path / "mopidy.conf",
    ]


def config_paths_display(value: list[Path]) -> str:
    return ", ".join(str(path) for path in value)


@Parameter(
    name="--config",
    help=(
        "Config files to use. "
        "Repeat parameter or separate values with colon to use multiple files. "
        "Later files have higher precedence."
    ),
    show_default=config_paths_display,
    negative="",
    n_tokens=1,
)
def config_paths_converter(_: type, tokens: Sequence[Token]) -> list[Path]:
    return [
        Path(path).expanduser() for token in tokens for path in token.value.split(":")
    ]


@Parameter(
    name=("--option", "-o"),
    help=(
        "Override config values. "
        "Repeat parameter to override multiple values. "
        "Format: SECTION/KEY=VALUE."
    ),
    negative="",
    n_tokens=1,
)
def config_overrides_converter(
    _: type, tokens: Sequence[Token]
) -> dict[str, dict[str, str]]:
    result = defaultdict(dict)
    for token in tokens:
        if "=" not in token.value:
            msg = f"Invalid config override: {token.value!r}"
            raise ValueError(msg)
        key, value = token.value.split("=", 1)
        if "/" not in key:
            msg = f"Invalid config override key: {key!r}"
            raise ValueError(msg)
        section, key = key.split("/", 1)
        result[section][key] = value
    return result


app = App(name="mopidy")
app.meta.group_parameters = Group("Global parameters", sort_key=0)


@app.meta.default
def launcher(
    *tokens: Annotated[
        str,
        Parameter(show=False, allow_leading_hyphen=True),
    ],
    config_paths: Annotated[
        list[Path],
        Parameter(converter=config_paths_converter),
    ] = config_paths_default(),  # noqa: B008
    config_overrides: Annotated[
        ConfigOverrides | None,
        Parameter(converter=config_overrides_converter),
    ] = None,
    quiet: Annotated[
        bool,
        Parameter(
            name=("--quiet", "-q"),
            help="Decrease amount of output to a minimum.",
            negative="",
        ),
    ] = False,
    verbosity_level: Annotated[
        int,
        Parameter(
            name=("--verbose", "-v"),
            help="Increase amount of output. Repeat up to four times for more.",
            count=True,
        ),
    ] = 0,
) -> None:
    """Common setup for all Mopidy commands.

    This function runs before the command specified on the command line.
    """
    try:
        # Get the extension manager that was created by early_setup()
        extensions = ExtensionManager.get_global()

        # Create default config file
        primary_config_path = config_paths[-1]
        if not primary_config_path.exists():
            default_config = ConfigLoader.only_defaults(extensions).validate()
            if default_config.write(
                path=primary_config_path,
                with_header=True,
                hide_secrets=False,
                comment_out_defaults=True,
            ):
                logger.info(
                    f"Initialized {primary_config_path.as_uri()} with default config"
                )

        # Resolve current config
        config_manager = ConfigLoader(
            paths=config_paths,
            overrides=config_overrides,
            extensions=extensions,
        ).validate()

        # Make the config manager available to the config command
        ConfigManager.set_global(config_manager)

        # Create application directories
        process.create_app_dirs(config_manager.config)

        # Start regular logging
        logs.setup_logging(
            config=config_manager.config,
            verbosity_level=-1 if quiet else verbosity_level,
        )

        # Check extensions
        for ext_name, error in extensions.check_config_and_env(
            config=config_manager.config,
            config_errors=config_manager.errors,
        ).items():
            if error is not None:
                config_manager.disable_extension(ext_name, comment=error)
        extensions.log_summary()
        if not extensions.with_status(ExtensionStatus.ENABLED):
            logger.error("No extensions enabled. Exiting...")
            sys.exit(1)

        # Check config
        config_manager.log_errors()
        if config_manager.app_errors:
            logger.error("Please fix fatal configuration errors. Exiting...")
            sys.exit(1)

        # Share the validated config globally
        Config.set_global(config_manager.config)

        # Run current command
        # Anything that wants to exit after this point muse use the exit_process()
        # helper as actors can have been started.
        app(tokens)
    except KeyboardInterrupt:
        return
    except Exception:
        logger.exception("Unhandled exception")
        raise


# Register all built-in, non-extension commands
app.default(server.command)
app.command(
    config.command,
    name="config",
    help="Display currently active configuration.",
)
app.command(
    deps.command,
    name="deps",
    help="Display installed extensions and their dependencies.",
)

# Register extension commands
if extensions := early_setup():
    extensions.init_commands(app)
