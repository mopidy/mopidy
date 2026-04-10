from __future__ import annotations

from typing import TYPE_CHECKING

from mopidy import config as config_lib
from mopidy._lib import paths

if TYPE_CHECKING:
    from pathlib import Path

    import cyclopts

    from mopidy.config import ConfigSchema

    from ._registry import Registry


class Extension:
    """Base class for Mopidy extensions."""

    dist_name: str
    """The extension's distribution name, as registered on PyPI

    Example: `mopidy-soundspot`
    """

    ext_name: str
    """The extension's short name, as used in setup.py and as config section
    name

    Example: `soundspot`
    """

    version: str
    """The extension's version.

    Should match the `__version__` attribute on the extension's main Python
    module and the version registered on PyPI.
    """

    def get_default_config(self) -> str:
        """The extension's default config as a text string."""
        msg = 'Add at least a config section with "enabled = true"'
        raise NotImplementedError(msg)

    def get_config_schema(self) -> ConfigSchema:
        """The extension's config validation schema."""
        schema = config_lib.ConfigSchema(self.ext_name)
        schema["enabled"] = config_lib.Boolean()
        return schema

    @classmethod
    def get_cache_dir(cls, config: config_lib.Config) -> Path:
        """Get or create cache directory for the extension.

        Use this directory to cache data that can safely be thrown away.
        """
        cache_dir_path = paths.expand_path(config["core"]["cache_dir"]) / cls.ext_name
        paths.get_or_create_dir(cache_dir_path)
        return cache_dir_path

    @classmethod
    def get_config_dir(cls, config: config_lib.Config) -> Path:
        """Get or create configuration directory for the extension."""
        config_dir_path = paths.expand_path(config["core"]["config_dir"]) / cls.ext_name
        paths.get_or_create_dir(config_dir_path)
        return config_dir_path

    @classmethod
    def get_data_dir(cls, config: config_lib.Config) -> Path:
        """Get or create data directory for the extension.

        Use this directory to store data that should be persistent.
        """
        data_dir_path = paths.expand_path(config["core"]["data_dir"]) / cls.ext_name
        paths.get_or_create_dir(data_dir_path)
        return data_dir_path

    def get_command(self) -> cyclopts.App | None:
        """Command to expose to command line users running `mopidy`.

        This method should return a `cyclopts.App` instance. The app will be
        mounted as the `mopidy <ext_name>` command. It can have subcommands on
        its own, e.g. `mopidy local scan`. Please refer to the cyclopts docs
        for details on how to implement this.

        /// note
        In Mopidy < 4.0, this method returned a custom `Command` class,
        which is no longer supported.
        ///
        """

    def validate_environment(self) -> None:
        """Check if the extension can run in the current environment.

        Dependencies described by `setup.py` are checked by Mopidy, so you
        should not check their presence here.

        If a problem is found, raise
        [ExtensionError][mopidy.exceptions.ExtensionError] with a message
        explaining the issue.

        Raises:
            ExtensionError: If the environment is not suitable.
        """

    def setup(self, registry: Registry) -> None:
        """Register the extension's components in the extension [Registry][].

        For example, to register a backend:

        ```python
        def setup(self, registry):
            from .backend import SoundspotBackend
            registry.add('backend', SoundspotBackend)
        ```

        See [Registry][] for a list of registry keys with a special meaning.
        Mopidy will instantiate and start any classes registered under the
        `frontend` and `backend` registry keys.

        This method can also be used for other setup tasks not involving the
        extension registry.

        Args:
            registry: The extension registry.
        """
        raise NotImplementedError
