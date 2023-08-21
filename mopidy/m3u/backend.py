from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pykka

from mopidy import backend
from mopidy.types import UriScheme

from . import playlists

if TYPE_CHECKING:
    from mopidy.audio import AudioProxy
    from mopidy.ext import Config


class M3UBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes: ClassVar[list[UriScheme]] = [UriScheme("m3u")]

    def __init__(
        self,
        config: Config,
        audio: AudioProxy,  # noqa: ARG002
    ) -> None:
        super().__init__()
        self.playlists = playlists.M3UPlaylistsProvider(self, config)
