import logging
from typing import ClassVar, override

import pykka

from mopidy import backend
from mopidy._lib import paths
from mopidy.audio import AudioProxy
from mopidy.config import Config
from mopidy.media import MediaReader
from mopidy.models import Track
from mopidy.types import DurationMs, Uri, UriScheme

from . import library
from .cue_library import CueTarget, split_cue_uri

logger = logging.getLogger(__name__)


class FileBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes: ClassVar[list[UriScheme]] = [UriScheme("file")]

    def __init__(self, *, config: Config, audio: AudioProxy) -> None:
        super().__init__(config=config, audio=audio)
        self._media_reader = MediaReader.create(
            config=config,
            timeout=DurationMs(config["file"]["metadata_timeout"]),
        )
        self.file_library = library.FileLibraryProvider(
            backend=self,
            config=config,
            media_reader=self._media_reader,
        )
        self.library = self.file_library
        self.playback = FilePlaybackProvider(audio=audio, backend=self)
        self.playlists = None

    @override
    def on_stop(self) -> None:
        self._media_reader.close()


class FilePlaybackProvider(backend.PlaybackProvider):
    backend: FileBackend

    @override
    def translate_uri(self, uri: Uri) -> Uri | None:
        if self._is_cue_uri(uri):
            cue_target = self._find_cue_target(uri)
            return paths.path_to_uri(cue_target.audio_path) if cue_target else None
        target = self.backend._media_reader.find_playback_target(uri)
        return target.uri if target else None

    @override
    def change_track(self, track: Track) -> bool:
        if not self._is_cue_uri(track.uri):
            return super().change_track(track)
        cue_target = self._find_cue_target(track.uri)
        if cue_target is None:
            logger.warning("Failed finding the CUE track %s", track.uri)
            return False

        # A track in a CUE sheet is a part of an audio file.
        uri = paths.path_to_uri(cue_target.audio_path)
        logger.debug(
            "Backend translated URI from %s to %s, from %s to %s",
            track.uri,
            uri,
            cue_target.start,
            cue_target.end,
        )
        self.audio.set_source_setup_callback(self.on_source_setup).get()
        self.audio.set_uri(
            uri,
            start=cue_target.start,
            end=cue_target.end,
        ).get()
        return True

    def _is_cue_uri(self, uri: Uri) -> bool:
        return self.backend.file_library.cue_library is not None and bool(
            split_cue_uri(uri)
        )

    def _find_cue_target(self, uri: Uri) -> CueTarget | None:
        cue_library = self.backend.file_library.cue_library
        return cue_library.find_target(uri) if cue_library else None
