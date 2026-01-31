from __future__ import annotations

import logging
from collections import UserDict
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from importlib.metadata import EntryPoint
from typing import TYPE_CHECKING, ClassVar, cast

from mopidy import exceptions
from mopidy.config import Config, types
from mopidy.ext import Extension

if TYPE_CHECKING:
    import cyclopts

    from mopidy._app.config import ConfigErrors
    from mopidy.config.schemas import ConfigSchema, MapConfigSchema

logger = logging.getLogger(__name__)


class ExtensionStatus(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    STOPPED_BY_LOAD_ERROR = "stopped_by_load_error"
    STOPPED_BY_CONFIG_ERROR = "stopped_by_config_error"
    STOPPED_BY_SELF_CHECK = "stopped_by_self_check"


@dataclass
class ExtensionRecord:
    ext_name: str
    entry_point: EntryPoint
    status: ExtensionStatus

    extension: Extension | None = None
    dist_name: str | None = None
    version: str | None = None
    config_schema: ConfigSchema | None = None
    config_defaults: str | None = None
    command: cyclopts.App | None = None

    @classmethod
    def load(cls, entry_point: EntryPoint) -> ExtensionRecord:
        if not (extension := cls._load_entry_point(entry_point)):
            return ExtensionRecord(
                ext_name=entry_point.name,
                entry_point=entry_point,
                status=ExtensionStatus.STOPPED_BY_LOAD_ERROR,
            )
        return cls._load_extension(entry_point, extension)

    @staticmethod
    def _load_entry_point(entry_point: EntryPoint) -> Extension | None:
        logger.debug(
            f"Loading {entry_point.group!r} entry point "
            f"{entry_point.name!r} from {entry_point.value!r}"
        )

        if entry_point.group != "mopidy.ext":
            logger.error(
                f"Entry point {entry_point.name!r} is in invalid group "
                f"{entry_point.group!r}, expected 'mopidy.ext'"
            )
            return None

        try:
            extension_class = entry_point.load()
        except Exception:
            logger.exception(
                f"Loading of extension entry point {entry_point.name!r} failed"
            )
            return None

        if not issubclass(extension_class, Extension):
            logger.error(
                f"Entry point {entry_point.name!r} did not contain "
                f"a valid extension class: {extension_class!r}"
            )
            return None

        extension_class = cast(type[Extension], extension_class)

        try:
            extension = extension_class()
        except Exception:
            logger.exception(
                f"Instantiating extension from entry point {entry_point.name!r} failed"
            )
            return None
        else:
            return extension

    @classmethod
    def _load_extension(
        cls,
        entry_point: EntryPoint,
        extension: Extension,
    ) -> ExtensionRecord:
        stopped_record = ExtensionRecord(
            ext_name=entry_point.name,
            entry_point=entry_point,
            status=ExtensionStatus.STOPPED_BY_LOAD_ERROR,
            extension=extension,
        )

        if extension.ext_name != entry_point.name:
            logger.error(
                f"Entry point name {entry_point.name!r} does not match "
                f"extension's ext_name {extension.ext_name!r}"
            )
            return stopped_record

        if not (config_schema := cls._load_config_schema(extension)):
            return stopped_record

        if not (config_defaults := extension.get_default_config()):
            logger.error(
                f"Extension {extension.ext_name!r} does not have a default config"
            )
            return stopped_record

        try:
            command = extension.get_command()
        except Exception:
            logger.exception(
                f"Loading command for extension {extension.ext_name!r} failed"
            )
            return stopped_record

        logger.debug("Loaded extension: %s %s", extension.dist_name, extension.version)
        return ExtensionRecord(
            ext_name=entry_point.name,
            entry_point=entry_point,
            status=ExtensionStatus.ENABLED,
            extension=extension,
            dist_name=extension.dist_name,
            version=extension.version,
            config_schema=config_schema,
            config_defaults=config_defaults,
            command=command,
        )

    @staticmethod
    def _load_config_schema(extension: Extension) -> ConfigSchema | None:
        if not (config_schema := extension.get_config_schema()):
            logger.error(
                f"Extension {extension.ext_name!r} does not have a config schema",
            )
            return None

        if not isinstance(config_schema.get("enabled"), types.Boolean):
            logger.error(
                f"Extension {extension.ext_name!r} does not have "
                "the required 'enabled' config option"
            )
            return None

        for key, value in config_schema.items():
            if not isinstance(value, types.ConfigValue):
                logger.error(
                    f"Extension {extension.ext_name!r} config schema contains "
                    f"an invalid value for the option {key!r}"
                )
                return None

        return config_schema

    def check_config_and_env(
        self,
        *,
        config: Config,
        config_errors: ConfigErrors,
    ) -> str | None:
        if self.status == ExtensionStatus.STOPPED_BY_LOAD_ERROR:
            return None  # Skip config checks until load errors are resolved.

        if not config[self.ext_name]["enabled"]:
            self.status = ExtensionStatus.DISABLED
            return "Extension disabled by user config"

        if config_errors.get(self.ext_name):
            self.status = ExtensionStatus.STOPPED_BY_CONFIG_ERROR
            return "Extension stopped due to config errors"

        if not self._self_check():
            self.status = ExtensionStatus.STOPPED_BY_SELF_CHECK
            return "Extension stopped by self-check"

        return None

    def _self_check(self) -> bool:
        if self.extension is None:
            return False
        logger.debug(f"Running {self.ext_name!r} extension self-check")
        try:
            self.extension.validate_environment()
        except exceptions.ExtensionError as exc:
            logger.info(f"Extension {self.ext_name!r} disabled by self-check: {exc}")
            return False
        except Exception:
            logger.exception(
                f"Extension {self.ext_name!r} self-check failed unexpectedly"
            )
            return False
        else:
            return True

    def init_command(self, app: cyclopts.App) -> None:
        if self.command is None:
            return
        try:
            app.command(self.command, name=self.ext_name)
        except Exception as e:
            logger.exception(
                "Registering command for extension %r failed: %s; skipping command",
                self.ext_name,
                e,
            )


class ExtensionManager(UserDict[str, ExtensionRecord]):
    _instance: ClassVar[ContextVar[ExtensionManager | None]] = ContextVar(
        "ExtensionManager", default=None
    )
    data: dict[str, ExtensionRecord]

    @classmethod
    def get_global(cls) -> ExtensionManager:
        if (instance := cls._instance.get()) is None:
            msg = f"{cls.__name__} not set in context"
            raise RuntimeError(msg)
        return instance

    @classmethod
    def set_global(cls, instance: ExtensionManager) -> None:
        if cls._instance.get() is not None:
            msg = f"{cls.__name__} already set in context"
            raise RuntimeError(msg)
        cls._instance.set(instance)

    @classmethod
    def discover(cls) -> ExtensionManager:
        result = {
            entry_point.name: record
            for entry_point in metadata.entry_points(group="mopidy.ext")
            if (record := ExtensionRecord.load(entry_point)) is not None
        }
        result = dict(sorted(result.items()))
        logger.debug("Discovered extensions: %s", ", ".join(result.keys()))
        return ExtensionManager(result)

    def with_status(self, *status: ExtensionStatus) -> dict[str, ExtensionRecord]:
        return {k: v for k, v in self.data.items() if v.status in status}

    @property
    def config_schemas(self) -> list[ConfigSchema | MapConfigSchema]:
        return [
            record.config_schema
            for record in self.data.values()
            if record.config_schema is not None
        ]

    @property
    def config_defaults(self) -> list[str]:
        return [
            record.config_defaults
            for record in self.data.values()
            if record.config_defaults is not None
        ]

    def check_config_and_env(
        self,
        *,
        config: Config,
        config_errors: ConfigErrors,
    ) -> dict[str, str | None]:
        errors: dict[str, str | None] = {}
        for record in self.data.values():
            errors[record.ext_name] = record.check_config_and_env(
                config=config,
                config_errors=config_errors,
            )
        return errors

    def log_summary(self) -> None:
        if names := self.with_status(ExtensionStatus.ENABLED).keys():
            logger.info(f"Enabled extensions: {', '.join(names)}")
        if names := self.with_status(ExtensionStatus.DISABLED).keys():
            logger.info(f"Disabled extensions: {', '.join(names)}")
        if names := self.with_status(ExtensionStatus.STOPPED_BY_LOAD_ERROR).keys():
            logger.warning(f"Extensions which failed to load: {', '.join(names)}")
        if names := self.with_status(ExtensionStatus.STOPPED_BY_CONFIG_ERROR).keys():
            logger.warning(f"Extensions with config errors: {', '.join(names)}")
        if names := self.with_status(ExtensionStatus.STOPPED_BY_SELF_CHECK).keys():
            logger.warning(f"Extensions which failed self-check: {', '.join(names)}")

    def init_commands(self, app: cyclopts.App) -> None:
        for record in self.with_status(ExtensionStatus.ENABLED).values():
            record.init_command(app)
