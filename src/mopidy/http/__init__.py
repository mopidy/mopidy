import logging
from pathlib import Path
from typing import cast

import mopidy
from mopidy import config, exceptions, ext
from mopidy.config import ConfigSchema

logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = "Mopidy-HTTP"
    ext_name = "http"
    version = mopidy.__version__

    def get_default_config(self) -> str:
        return config.read(Path(__file__).parent / "ext.conf")

    def get_config_schema(self) -> ConfigSchema:
        schema = super().get_config_schema()
        schema["hostname"] = config.Hostname()
        schema["port"] = config.Port()
        schema["static_dir"] = config.Deprecated()
        schema["zeroconf"] = config.String(optional=True)
        schema["allowed_origins"] = config.List(
            optional=True,
            unique=True,
            subtype=config.String(transformer=lambda x: x.lower()),
        )
        schema["csrf_protection"] = config.Boolean(optional=True)
        schema["default_app"] = config.String(optional=True)
        return schema

    def validate_environment(self) -> None:
        try:
            import tornado.web  # noqa: F401 (Imported to test if available)
        except ImportError as exc:
            msg = "tornado library not found"
            raise exceptions.ExtensionError(msg) from exc

    def setup(self, registry: ext.Registry) -> None:
        from .actor import HttpFrontend
        from .handlers import make_mopidy_app_factory
        from .types import HttpApp, HttpStatic

        HttpFrontend.apps = cast(list[HttpApp], registry["http:app"])
        HttpFrontend.statics = cast(list[HttpStatic], registry["http:static"])

        registry.add("frontend", HttpFrontend)
        registry.add(
            "http:app",
            {
                "name": "mopidy",
                "factory": make_mopidy_app_factory(
                    apps=cast(list[HttpApp], registry["http:app"]),
                    statics=cast(list[HttpStatic], registry["http:static"]),
                ),
            },
        )
