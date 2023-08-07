from pathlib import Path

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):
    dist_name = "Mopidy-SoftwareMixer"
    ext_name = "softwaremixer"
    version = mopidy.__version__

    def get_default_config(self):
        return config.read(Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        return super().get_config_schema()

    def setup(self, registry):
        from .mixer import SoftwareMixer

        registry.add("mixer", SoftwareMixer)
