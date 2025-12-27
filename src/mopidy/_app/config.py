from __future__ import annotations

import configparser
import logging
import os
import re
import textwrap
from collections.abc import Generator
from contextvars import ContextVar
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar

import mopidy
from mopidy._app.extensions import ExtensionManager, ExtensionStatus
from mopidy._lib import paths
from mopidy.config import Config, read, types
from mopidy.config.schemas import ConfigSchema, MapConfigSchema

logger = logging.getLogger(__name__)


def command() -> None:
    config_manager = ConfigManager.get_global()
    print(  # noqa: T201
        config_manager.format(
            with_header=False,
            hide_secrets=True,
            comment_out_defaults=False,
        )
    )


app_schemas: list[ConfigSchema | MapConfigSchema] = [
    ConfigSchema(
        "core",
        {
            "cache_dir": types.Path(),
            "config_dir": types.Path(),
            "data_dir": types.Path(),
            #
            # MPD supports at most 10k tracks, some clients segfault when this
            # is exceeded.
            "max_tracklist_length": types.Integer(minimum=1),
            "restore_state": types.Boolean(optional=True),
        },
    ),
    ConfigSchema(
        "logging",
        {
            "verbosity": types.Integer(minimum=-1, maximum=4),
            "format": types.String(),
            "color": types.Boolean(),
            "config_file": types.Path(optional=True),
        },
    ),
    MapConfigSchema(
        "loglevels",
        types.LogLevel(),
    ),
    MapConfigSchema(
        "logcolors",
        types.LogColor(),
    ),
    ConfigSchema(
        "audio",
        {
            "mixer": types.String(),
            "mixer_volume": types.Integer(optional=True, minimum=0, maximum=100),
            "output": types.String(),
            "buffer_time": types.Integer(optional=True, minimum=1),
        },
    ),
    ConfigSchema(
        "proxy",
        {
            "scheme": types.String(
                optional=True,
                choices=("http", "https", "socks4", "socks5"),
            ),
            "hostname": types.Hostname(optional=True),
            "port": types.Port(optional=True),
            "username": types.String(optional=True),
            "password": types.Secret(optional=True),
        },
    ),
]


type ConfigDict = dict[str, dict[str, Any]]
type ConfigErrors = dict[str, dict[str, str]]
type ConfigOverrides = dict[str, dict[str, str]]


class ConfigLoader:
    def __init__(
        self,
        *,
        paths: list[Path],
        overrides: ConfigOverrides | None = None,
        extensions: ExtensionManager,
    ) -> None:
        self._paths = paths
        self._overrides: ConfigOverrides = overrides or {}
        self._extensions = extensions

    @classmethod
    def only_defaults(cls, extensions: ExtensionManager | None) -> ConfigLoader:
        if extensions is None:
            extensions = ExtensionManager()  # Empty extension manager
        return cls(
            paths=[],  # Ignore existing config files
            overrides=None,  # Ignore all overrides
            extensions=extensions,
        )

    @cached_property
    def _config_defaults(self) -> list[str]:
        return [
            read(Path(__file__).parent / "default.conf"),
            *self._extensions.config_defaults,
        ]

    @cached_property
    def _config_schemas(self) -> list[ConfigSchema | MapConfigSchema]:
        return [
            *app_schemas,
            *self._extensions.config_schemas,
        ]

    @cached_property
    def raw_config(self) -> ConfigDict:
        parser = configparser.RawConfigParser(inline_comment_prefixes=(";",))

        # TODO: simply return path to config file for defaults so we can load it
        # all in the same way?
        logger.debug("Loading config from builtin defaults")
        for default in self._config_defaults:
            if isinstance(default, bytes):
                default = default.decode()
            parser.read_string(default)

        # Load config from a series of config files
        for path in self._paths:
            path = paths.expand_path(path)
            # TODO: Drop support for directories?
            if path.is_dir():
                for entry in path.iterdir():
                    if entry.is_file() and entry.suffix == ".conf":
                        self._read_config_file(parser, entry)
            else:
                self._read_config_file(parser, path)

        if self._overrides:
            logger.info("Loading config from command line options")
            parser.read_dict(self._overrides)

        return {section: dict(parser.items(section)) for section in parser.sections()}

    def _read_config_file(
        self,
        parser: configparser.RawConfigParser,
        file_path: Path,
    ) -> None:
        if not file_path.exists():
            logger.debug(
                f"Loading config from {file_path.as_uri()} failed; it does not exist"
            )
            return
        if not os.access(str(file_path), os.R_OK):
            logger.warning(
                f"Loading config from {file_path.as_uri()} failed; "
                "read permission missing"
            )
            return

        try:
            logger.info(f"Loading config from {file_path.as_uri()}")
            with file_path.open("r") as fh:
                parser.read_file(fh)
        except configparser.MissingSectionHeaderError:
            logger.warning(
                f"Loading config from {file_path.as_uri()} failed; "
                f"it does not have a config section",
            )
        except configparser.ParsingError as e:
            linenos = ", ".join(str(lineno) for lineno, line in e.errors)
            logger.warning(
                f"Config file {file_path.as_uri()} has errors; "
                f"line {linenos} has been ignored",
            )
        except OSError:
            # TODO: if this is the initial load of logging config we might not
            # have a logger at this point, we might want to handle this better.
            logger.debug(f"Config file {file_path.as_uri()} not found; skipping")

    def validate(self) -> ConfigManager:
        validated_config: ConfigDict = {}
        errors: ConfigErrors = {}

        for schema in self._config_schemas:
            values = self.raw_config.get(schema.name, {})
            result, error = schema.deserialize(values)
            if error:
                errors[schema.name] = error
            if result:
                validated_config[schema.name] = result

        schemaless_sections = set(self.raw_config) - {
            schema.name for schema in self._config_schemas
        }
        for section in schemaless_sections:
            logger.debug(
                f"Skipping validation of config section {section!r} "
                f"because no matching extension is loaded"
            )

        return ConfigManager(
            extensions=self._extensions,
            config_schemas=self._config_schemas,
            config=validated_config,
            errors=errors,
        )


class ConfigManager:
    _instance: ClassVar[ContextVar[ConfigManager | None]] = ContextVar(
        "ConfigManager", default=None
    )

    @classmethod
    def get_global(cls) -> ConfigManager:
        if (instance := cls._instance.get()) is None:
            msg = f"{cls} not set in context"
            raise RuntimeError(msg)
        return instance

    @classmethod
    def set_global(cls, instance: ConfigManager) -> None:
        if cls._instance.get() is not None:
            msg = f"{cls} already set in context"
            raise RuntimeError(msg)
        cls._instance.set(instance)

    def __init__(
        self,
        *,
        extensions: ExtensionManager,
        config_schemas: list[ConfigSchema | MapConfigSchema],
        config: ConfigDict,
        errors: ConfigErrors,
    ) -> None:
        self._extensions = extensions
        self._config_schemas = config_schemas
        self._config = config
        self.errors = errors

    def disable_extension(self, ext_name: str, comment: str) -> None:
        if ext_name not in self._config:
            self._config[ext_name] = {}
        self._config[ext_name]["enabled"] = False
        if ext_name not in self.errors:
            self.errors[ext_name] = {}
        self.errors[ext_name]["enabled"] = comment

    @property
    def config(self) -> Config:
        return Config(self._config)

    @property
    def app_errors(self) -> ConfigErrors:
        return {k: v for k, v in self.errors.items() if k not in self._extensions and v}

    @property
    def extension_errors(self) -> ConfigErrors:
        return {k: v for k, v in self.errors.items() if k in self._extensions and v}

    def log_errors(self) -> None:
        for section in sorted(self.app_errors):
            logger.warning(f"Found fatal {section!r} configuration errors:")
            for field, msg in self.errors[section].items():
                logger.warning(f"  {section}/{field}: {msg}")

        for section in sorted(self.extension_errors):
            status = self._extensions[section].status
            if status == ExtensionStatus.DISABLED:
                continue
            logger.warning(
                f"Found {section!r} configuration errors. "
                f"The extension has been automatically disabled:",
            )
            for field, msg in self.errors[section].items():
                logger.warning(f"  {section}/{field}: {msg}")

    def write(
        self,
        *,
        path: Path,
        with_header: bool = False,
        hide_secrets: bool = True,
        comment_out_defaults: bool = False,
    ) -> bool:
        try:
            paths.get_or_create_file(
                path,
                mkdir=True,
                content=self.format(
                    with_header=with_header,
                    hide_secrets=hide_secrets,
                    comment_out_defaults=comment_out_defaults,
                ),
            )
        except OSError as exc:
            logger.warning(f"Unable to write config to {path.as_uri()}: {exc}")
            return False
        else:
            return True

    def format(
        self,
        *,
        with_header: bool = False,
        hide_secrets: bool = True,
        comment_out_defaults: bool = False,
    ) -> str:
        result = "\n".join(
            self._format_generator(
                with_header=with_header,
                hide_secrets=hide_secrets,
                comment_out_defaults=comment_out_defaults,
            )
        )

        # Throw away all bytes that are not valid UTF-8
        return result.encode(errors="surrogateescape").decode(errors="replace")

    def _format_generator(
        self,
        *,
        with_header: bool,
        hide_secrets: bool,
        comment_out_defaults: bool,
    ) -> Generator[str]:
        if with_header:
            versions = [
                f"mopidy {mopidy.__version__}",
                *[
                    f"{r.extension.dist_name} {r.extension.version}"
                    for r in self._extensions.values()
                    if r.extension is not None
                ],
            ]
            yield textwrap.dedent(f"""\
                # For further information about options in this file see:
                #   https://docs.mopidy.com/
                #
                # The initial commented out values reflect the defaults as of:
                #   {"\n#   ".join(versions)}
                #
                # Available options and defaults might have changed since then,
                # run `mopidy config` to see the current effective config and
                # `mopidy --version` to check the current version.
                """)

        for schema in self._config_schemas:
            serialized = schema.serialize(
                self.config.get(schema.name, {}),
                display=hide_secrets,
            )
            if not serialized:
                continue
            yield f"[{schema.name}]"
            for key, value in serialized.items():
                if isinstance(value, types.DeprecatedValue):
                    continue
                line = f"{key} ="
                if value is not None:
                    line += " " + value
                if error := self.errors.get(schema.name, {}).get(key):
                    line += "  ; " + error.capitalize()
                if comment_out_defaults:
                    line = re.sub(r"^", "#", line, flags=re.MULTILINE)
                yield line
            yield ""
