# ruff: noqa: ARG002

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pykka
from pykka.typing import proxy_method

if TYPE_CHECKING:
    from mopidy._lib.gi import Gst
    from mopidy.audio import AudioProxy
    from mopidy.models import Track
    from mopidy.types import DurationMs, Uri

    from ._backend import Backend


logger = logging.getLogger(__name__)


@pykka.traversable
class PlaybackProvider:
    """A playback provider provides audio playback control.

    :param audio: the audio actor
    :param backend: the backend
    """

    def __init__(self, audio: AudioProxy, backend: Backend) -> None:
        self.audio = audio
        self.backend = backend

    def pause(self) -> bool:
        """Pause playback.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.pause_playback().get()

    def play(self) -> bool:
        """Start playback.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.start_playback().get()

    def prepare_change(self) -> None:
        """Indicate that an URI change is about to happen.

        *MAY be reimplemented by subclass.*

        It is extremely unlikely it makes sense for any backends to override
        this. For most practical purposes it should be considered an internal
        call between backends and core that backend authors should not touch.
        """
        self.audio.prepare_change().get()

    def translate_uri(self, uri: Uri) -> Uri | None:
        """Convert custom URI scheme to real playable URI.

        *MAY be reimplemented by subclass.*

        This is very likely the *only* thing you need to override as a backend
        author. Typically this is where you convert any Mopidy specific URI
        to a real URI and then return it. If you can't convert the URI just
        return :class:`None`.

        :param uri: the URI to translate
        """
        return uri

    def is_live(self, uri: Uri) -> bool:
        """Decide if the URI should be treated as a live stream or not.

        *MAY be reimplemented by subclass.*

        Playing a source as a live stream disables buffering, which reduces
        latency before playback starts, and discards data when paused.

        :param uri: the URI
        """
        return False

    def should_download(self, uri: Uri) -> bool:
        """Attempt progressive download buffering for the URI or not.

        *MAY be reimplemented by subclass.*

        When streaming a fixed length file, the entire file can be buffered
        to improve playback performance.

        :param uri: the URI
        """
        return False

    def on_source_setup(self, source: Gst.Element) -> None:
        """Called when a new GStreamer source is created, allowing us to configure
        the source. This runs in the audio thread so should not block.

        *MAY be reimplemented by subclass.*

        :param source: the GStreamer source element

        .. versionadded:: 3.4
        """

    def change_track(self, track: Track) -> bool:
        """Switch to provided track.

        *MAY be reimplemented by subclass.*

        It is unlikely it makes sense for any backends to override
        this. For most practical purposes it should be considered an internal
        call between backends and core that backend authors should not touch.

        The default implementation will call :meth:`translate_uri` which
        is what you want to implement.

        :param track: the track to play
        """
        uri = self.translate_uri(track.uri)
        if uri != track.uri:
            logger.debug("Backend translated URI from %s to %s", track.uri, uri)
        if uri is None:
            return False
        self.audio.set_source_setup_callback(self.on_source_setup).get()
        self.audio.set_uri(
            uri,
            live_stream=self.is_live(uri),
            download=self.should_download(uri),
        ).get()
        return True

    def resume(self) -> bool:
        """Resume playback at the same time position playback was paused.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.start_playback().get()

    def seek(self, time_position: DurationMs) -> bool:
        """Seek to a given time position.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.

        :param time_position: time position in milliseconds
        """
        return self.audio.set_position(time_position).get()

    def stop(self) -> bool:
        """Stop playback.

        *MAY be reimplemented by subclass.*

        Should not be used for tracking if tracks have been played or when we
        are done playing them.

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.stop_playback().get()

    def get_time_position(self) -> DurationMs:
        """Get the current time position in milliseconds.

        *MAY be reimplemented by subclass.*
        """
        return self.audio.get_position().get()


class PlaybackProviderProxy:
    pause = proxy_method(PlaybackProvider.pause)
    play = proxy_method(PlaybackProvider.play)
    prepare_change = proxy_method(PlaybackProvider.prepare_change)
    translate_uri = proxy_method(PlaybackProvider.translate_uri)
    is_live = proxy_method(PlaybackProvider.is_live)
    should_download = proxy_method(PlaybackProvider.should_download)
    on_source_setup = proxy_method(PlaybackProvider.on_source_setup)
    change_track = proxy_method(PlaybackProvider.change_track)
    resume = proxy_method(PlaybackProvider.resume)
    seek = proxy_method(PlaybackProvider.seek)
    stop = proxy_method(PlaybackProvider.stop)
    get_time_position = proxy_method(PlaybackProvider.get_time_position)
