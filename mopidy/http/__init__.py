import logging
import os

import mopidy
from mopidy import config as config_lib
from mopidy import exceptions, ext

logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = "Mopidy-HTTP"
    ext_name = "http"
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), "ext.conf")
        return config_lib.read(conf_file)

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["hostname"] = config_lib.Hostname()
        schema["port"] = config_lib.Port()
        schema["static_dir"] = config_lib.Deprecated()
        schema["zeroconf"] = config_lib.String(optional=True)
        schema["allowed_origins"] = config_lib.List(
            optional=True,
            unique=True,
            subtype=config_lib.String(transformer=lambda x: x.lower()),
        )
        schema["csrf_protection"] = config_lib.Boolean(optional=True)
        schema["default_app"] = config_lib.String(optional=True)
        return schema

    def validate_environment(self):
        try:
            import tornado.web  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError("tornado library not found", e)

    def setup(self, registry):
        from .actor import HttpFrontend
        from .handlers import make_mopidy_app_factory

        HttpFrontend.apps = registry["http:app"]
        HttpFrontend.statics = registry["http:static"]

        registry.add("frontend", HttpFrontend)
        registry.add(
            "http:app",
            {
                "name": "mopidy",
                "factory": make_mopidy_app_factory(
                    registry["http:app"], registry["http:static"]
                ),
            },
        )
