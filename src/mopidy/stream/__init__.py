from pathlib import Path

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):
    dist_name = "Mopidy-Stream"
    ext_name = "stream"
    version = mopidy.__version__

    def get_default_config(self):
        return config.read(Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["protocols"] = config.List()
        schema["metadata_blacklist"] = config.List(optional=True)
        schema["timeout"] = config.Integer(minimum=1000, maximum=1000 * 60 * 60)
        return schema

    def validate_environment(self):
        pass

    def setup(self, registry):
        from .actor import StreamBackend

        registry.add("backend", StreamBackend)
