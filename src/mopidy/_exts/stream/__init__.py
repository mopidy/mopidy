from pathlib import Path
from typing import override

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):
    dist_name = "mopidy-stream"
    ext_name = "stream"
    version = mopidy.__version__

    def get_default_config(self) -> str:
        return config.read(Path(__file__).parent / "ext.conf")

    @override
    def get_config_schema(self) -> config.ConfigSchema:
        schema = super().get_config_schema()
        schema["protocols"] = config.List()
        schema["metadata_blacklist"] = config.List(optional=True)
        schema["timeout"] = config.Integer(minimum=1000, maximum=1000 * 60 * 60)
        return schema

    @override
    def setup(self, registry: ext.Registry) -> None:
        from .actor import StreamBackend  # noqa: PLC0415

        registry.add("backend", StreamBackend)
