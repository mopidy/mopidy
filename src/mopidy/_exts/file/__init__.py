import logging
from pathlib import Path
from typing import override

import mopidy
from mopidy import config, ext

logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = "mopidy-file"
    ext_name = "file"
    version = mopidy.__version__

    def get_default_config(self) -> str:
        return config.read(Path(__file__).parent / "ext.conf")

    def get_config_schema(self) -> config.ConfigSchema:
        schema = super().get_config_schema()
        schema["media_dirs"] = config.List(optional=True)
        schema["excluded_file_extensions"] = config.List(optional=True)
        schema["show_dotfiles"] = config.Boolean(optional=True)
        schema["follow_symlinks"] = config.Boolean(optional=True)
        schema["metadata_timeout"] = config.Integer(optional=True)
        return schema

    @override
    def setup(self, registry: ext.Registry) -> None:
        from .backend import FileBackend  # noqa: PLC0415

        registry.add("backend", FileBackend)
