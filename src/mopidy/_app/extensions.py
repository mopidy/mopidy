from __future__ import annotations

import logging
from importlib import metadata
from typing import TYPE_CHECKING, Any, NamedTuple, TypedDict

from mopidy import config as config_lib
from mopidy import exceptions
from mopidy.ext import Extension

if TYPE_CHECKING:
    from mopidy.commands import Command

logger = logging.getLogger(__name__)


class ExtensionsStatus(TypedDict):
    validate: list[Extension]
    config: list[Extension]
    disabled: list[Extension]
    enabled: list[Extension]


class ExtensionData(NamedTuple):
    extension: Extension
    entry_point: Any
    config_schema: config_lib.ConfigSchema
    config_defaults: Any
    command: Command | None


def load_extensions() -> list[ExtensionData]:
    """Find all installed extensions.

    :returns: list of installed extensions
    """
    installed_extensions = []

    for entry_point in metadata.entry_points(group="mopidy.ext"):
        logger.debug("Loading entry point: %s", entry_point)
        try:
            extension_class = entry_point.load()
        except Exception:
            logger.exception(f"Failed to load extension {entry_point.name}.")
            continue

        try:
            if not issubclass(extension_class, Extension):
                raise TypeError  # noqa: TRY301
        except TypeError:
            logger.error(
                "Entry point %s did not contain a valid extension class: %r",
                entry_point.name,
                extension_class,
            )
            continue

        try:
            extension = extension_class()
            # Ensure required extension attributes are present after try block
            _ = extension.dist_name
            _ = extension.ext_name
            _ = extension.version
            extension_data = ExtensionData(
                entry_point=entry_point,
                extension=extension,
                config_schema=extension.get_config_schema(),
                config_defaults=extension.get_default_config(),
                command=extension.get_command(),
            )
        except Exception:
            logger.exception(
                "Setup of extension from entry point %s failed, ignoring extension.",
                entry_point.name,
            )
            continue

        installed_extensions.append(extension_data)

        logger.debug("Loaded extension: %s %s", extension.dist_name, extension.version)

    names = (ed.extension.ext_name for ed in installed_extensions)
    logger.debug("Discovered extensions: %s", ", ".join(names))
    return installed_extensions


def validate_extension_data(data: ExtensionData) -> bool:  # noqa: PLR0911
    """Verify extension's dependencies and environment.

    :param data: an extension to check
    :returns: if extension should be run
    """
    logger.debug("Validating extension: %s", data.extension.ext_name)

    if data.extension.ext_name != data.entry_point.name:
        logger.warning(
            "Disabled extension %(ep)s: entry point name (%(ep)s) "
            "does not match extension name (%(ext)s)",
            {"ep": data.entry_point.name, "ext": data.extension.ext_name},
        )
        return False

    try:
        data.entry_point.load()
    except ModuleNotFoundError as exc:
        logger.info(
            "Disabled extension %s: Exception %s",
            data.extension.ext_name,
            exc,
        )
        # Remark: There are no version check, so any version is accepted
        # this is a difference to pkg_resources, and affect debugging.
        return False

    try:
        data.extension.validate_environment()
    except exceptions.ExtensionError as exc:
        logger.info("Disabled extension %s: %s", data.extension.ext_name, exc)
        return False
    except Exception:
        logger.exception(
            "Validating extension %s failed with an exception.",
            data.extension.ext_name,
        )
        return False

    if not data.config_schema:
        logger.error(
            "Extension %s does not have a config schema, disabling.",
            data.extension.ext_name,
        )
        return False

    if not isinstance(data.config_schema.get("enabled"), config_lib.Boolean):
        logger.error(
            'Extension %s does not have the required "enabled" config'
            " option, disabling.",
            data.extension.ext_name,
        )
        return False

    for key, value in data.config_schema.items():
        if not isinstance(value, config_lib.ConfigValue):
            logger.error(
                "Extension %s config schema contains an invalid value"
                ' for the option "%s", disabling.',
                data.extension.ext_name,
                key,
            )
            return False

    if not data.config_defaults:
        logger.error(
            "Extension %s does not have a default config, disabling.",
            data.extension.ext_name,
        )
        return False

    return True
