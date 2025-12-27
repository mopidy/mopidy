from pathlib import Path
from typing import override

import mopidy
from mopidy import config, ext


class Extension(ext.Extension):
    dist_name = "mopidy-softwaremixer"
    ext_name = "softwaremixer"
    version = mopidy.__version__

    @override
    def get_default_config(self) -> str:
        return config.read(Path(__file__).parent / "ext.conf")

    @override
    def setup(self, registry: ext.Registry) -> None:
        from .mixer import SoftwareMixer  # noqa: PLC0415

        registry.add("mixer", SoftwareMixer)
