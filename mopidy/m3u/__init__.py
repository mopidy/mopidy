import logging
from pathlib import Path

import mopidy
from mopidy import config, ext
from mopidy.config import ConfigSchema

logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = "Mopidy-M3U"
    ext_name = "m3u"
    version = mopidy.__version__

    def get_default_config(self) -> str:
        return config.read(Path(__file__).parent / "ext.conf")

    def get_config_schema(self) -> ConfigSchema:
        schema = super().get_config_schema()
        schema["base_dir"] = config.Path(optional=True)
        schema["default_encoding"] = config.String()
        schema["default_extension"] = config.String(choices=[".m3u", ".m3u8"])
        schema["playlists_dir"] = config.Path(optional=True)
        return schema

    def setup(self, registry: ext.Registry) -> None:
        from .backend import M3UBackend

        registry.add("backend", M3UBackend)
