import os

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):

    dist_name = "Mopidy-SoftwareMixer"
    ext_name = "softwaremixer"
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), "ext.conf")
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["min_volume"] = config.Integer(minimum=0, maximum=100)
        schema["max_volume"] = config.Integer(minimum=0, maximum=100)
        schema["volume_scale"] = config.String(
            choices=("linear", "exp")
        )
        schema["volume_exp"] = config.Float(minimum=1, maximum=3)
        return schema

    def setup(self, registry):
        from .mixer import SoftwareMixer

        registry.add("mixer", SoftwareMixer)
