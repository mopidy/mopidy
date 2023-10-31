import logging
from pathlib import Path

import mopidy
from mopidy import config, ext

logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = "Mopidy-File"
    ext_name = "file"
    version = mopidy.__version__

    def get_default_config(self):
        return config.read(Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["media_dirs"] = config.List(optional=True)
        schema["excluded_file_extensions"] = config.List(optional=True)
        schema["show_dotfiles"] = config.Boolean(optional=True)
        schema["follow_symlinks"] = config.Boolean(optional=True)
        schema["metadata_timeout"] = config.Integer(optional=True)
        return schema

    def setup(self, registry):
        from .backend import FileBackend

        registry.add("backend", FileBackend)
