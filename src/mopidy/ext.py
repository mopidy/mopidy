from __future__ import annotations

import logging
from collections.abc import Mapping
from importlib import metadata
from typing import TYPE_CHECKING, NamedTuple

from mopidy import config as config_lib
from mopidy import exceptions
from mopidy.internal import path

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path
    from typing import Any, TypeAlias

    from mopidy.commands import Command
    from mopidy.config import ConfigSchema

    Config = dict[str, dict[str, Any]]
    RegistryEntry: TypeAlias = type[Any] | dict[str, Any]

logger = logging.getLogger(__name__)


class ExtensionData(NamedTuple):
    extension: Extension
    entry_point: Any
    config_schema: ConfigSchema
    config_defaults: Any
    command: Command | None


class Extension:
    """Base class for Mopidy extensions."""

    dist_name: str
    """The extension's distribution name, as registered on PyPI

    Example: ``Mopidy-Soundspot``
    """

    ext_name: str
    """The extension's short name, as used in setup.py and as config section
    name

    Example: ``soundspot``
    """

    version: str
    """The extension's version

    Should match the :attr:`__version__` attribute on the extension's main
    Python module and the version registered on PyPI.
    """

    def get_default_config(self) -> str:
        """The extension's default config as a text string.

        :returns: str
        """
        msg = 'Add at least a config section with "enabled = true"'
        raise NotImplementedError(msg)

    def get_config_schema(self) -> ConfigSchema:
        """The extension's config validation schema.

        :returns: :class:`~mopidy.config.schemas.ConfigSchema`
        """
        schema = config_lib.ConfigSchema(self.ext_name)
        schema["enabled"] = config_lib.Boolean()
        return schema

    @classmethod
    def check_attr(cls) -> None:
        """Check if ext_name exist."""
        if not hasattr(cls, "ext_name") or cls.ext_name is None:
            msg = f"{cls} not an extension or ext_name missing!"
            raise AttributeError(msg)

    @classmethod
    def get_cache_dir(cls, config: Config) -> Path:
        """Get or create cache directory for the extension.

        Use this directory to cache data that can safely be thrown away.

        :param config: the Mopidy config object
        :return: pathlib.Path
        """
        cls.check_attr()
        cache_dir_path = path.expand_path(config["core"]["cache_dir"]) / cls.ext_name
        path.get_or_create_dir(cache_dir_path)
        return cache_dir_path

    @classmethod
    def get_config_dir(cls, config: Config) -> Path:
        """Get or create configuration directory for the extension.

        :param config: the Mopidy config object
        :return: pathlib.Path
        """
        cls.check_attr()
        config_dir_path = path.expand_path(config["core"]["config_dir"]) / cls.ext_name
        path.get_or_create_dir(config_dir_path)
        return config_dir_path

    @classmethod
    def get_data_dir(cls, config: Config) -> Path:
        """Get or create data directory for the extension.

        Use this directory to store data that should be persistent.

        :param config: the Mopidy config object
        :returns: pathlib.Path
        """
        cls.check_attr()
        data_dir_path = path.expand_path(config["core"]["data_dir"]) / cls.ext_name
        path.get_or_create_dir(data_dir_path)
        return data_dir_path

    def get_command(self) -> Command | None:
        """Command to expose to command line users running ``mopidy``.

        :returns:
          Instance of a :class:`~mopidy.commands.Command` class.
        """

    def validate_environment(self) -> None:
        """Checks if the extension can run in the current environment.

        Dependencies described by :file:`setup.py` are checked by Mopidy, so
        you should not check their presence here.

        If a problem is found, raise :exc:`~mopidy.exceptions.ExtensionError`
        with a message explaining the issue.

        :raises: :exc:`~mopidy.exceptions.ExtensionError`
        :returns: :class:`None`
        """

    def setup(self, registry: Registry) -> None:
        """Register the extension's components in the extension :class:`Registry`.

        For example, to register a backend::

            def setup(self, registry):
                from .backend import SoundspotBackend
                registry.add('backend', SoundspotBackend)

        See :class:`Registry` for a list of registry keys with a special
        meaning. Mopidy will instantiate and start any classes registered under
        the ``frontend`` and ``backend`` registry keys.

        This method can also be used for other setup tasks not involving the
        extension registry.

        :param registry: the extension registry
        :type registry: :class:`Registry`
        """
        raise NotImplementedError


class Registry(Mapping):
    """Registry of components provided by Mopidy extensions.

    Passed to the :meth:`~Extension.setup` method of all extensions. The
    registry can be used like a dict of string keys and lists.

    Some keys have a special meaning, including, but not limited to:

    - ``backend`` is used for Mopidy backend classes.
    - ``frontend`` is used for Mopidy frontend classes.

    Extensions can use the registry for allow other to extend the extension
    itself. For example the ``Mopidy-Local`` historically used the
    ``local:library`` key to allow other extensions to register library
    providers for ``Mopidy-Local`` to use. Extensions should namespace
    custom keys with the extension's :attr:`~Extension.ext_name`,
    e.g. ``local:foo`` or ``http:bar``.
    """

    def __init__(self) -> None:
        self._registry: dict[str, list[RegistryEntry]] = {}

    def add(self, name: str, entry: RegistryEntry) -> None:
        """Add a component to the registry.

        Multiple classes can be registered to the same name.
        """
        self._registry.setdefault(name, []).append(entry)

    def __getitem__(self, name: str) -> list[RegistryEntry]:
        return self._registry.setdefault(name, [])

    def __iter__(self) -> Iterator[str]:
        return iter(self._registry)

    def __len__(self) -> int:
        return len(self._registry)


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
