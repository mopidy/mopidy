# ruff: noqa: ARG002

from typing import ClassVar

import pykka

from mopidy import backend

from . import playlists


class M3UBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes: ClassVar[list[str]] = ["m3u"]

    def __init__(self, config, audio):
        super().__init__()
        self.playlists = playlists.M3UPlaylistsProvider(self, config)
