from __future__ import annotations

from typing import TYPE_CHECKING

import pykka

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.mixer import MixerProxy
    from mopidy.types import DurationMs


class AudioBase(pykka.ThreadingActor):
    _config: Config
    _mixer: MixerProxy | None

    def __init__(
        self,
        config: Config,
        mixer: MixerProxy | None,
    ) -> None:
        super().__init__()
        self._config = config
        self._mixer = mixer

    def set_uri(self, uri: str, live_stream: bool, download: bool) -> None:
        """Set URI of audio to be played.

        You *MUST* call :meth:`prepare_change` before calling this method.

        :param uri: the URI to play
        :param live_stream: disables buffering, reducing latency for stream,
            and discarding data when paused
        :param download: enables "download" buffering mode
        """
        msg = f"{self.__class__.__name__} must implement set_uri"
        raise NotImplementedError(msg)

    def set_source_setup_callback(self, callback):
        """Configure audio to use a source-setup callback.

        This should be used to modify source-specific properties such as login
        details.

        :param callable: Callback to run when we setup the source.
        """

    def set_about_to_finish_callback(self, callback):
        """Configure audio to use an about-to-finish callback.

        This should be used to achieve gapless playback. For this to work the
        callback *MUST* call :meth:`set_uri` with the new URI to play and
        block until this call has been made. :meth:`prepare_change` is not
        needed before :meth:`set_uri` in this one special case.

        :param callable: Callback to run when we need the next URI.
        """

    def get_position(self) -> int:
        """Get position in milliseconds."""
        return 0

    def set_position(self, position: DurationMs) -> bool:  # noqa: ARG002
        """Set position in milliseconds.

        :param position: the position in milliseconds
        """
        return False

    def start_playback(self) -> bool:
        """Notify GStreamer that it should start playback.

        Returns :class:`True` if successful, else :class:`False`.
        """
        return False

    def pause_playback(self) -> bool:
        """Notify GStreamer that it should pause playback.

        Returns :class:`True` if successful, else :class:`False`.
        """
        return False

    def prepare_change(self) -> bool:
        """Notify GStreamer that we are about to change state of playback.

        This function *MUST* be called before changing URIs or doing
        changes like updating data that is being pushed. The reason for this
        is that GStreamer will reset all its state when it changes to
        :attr:`Gst.State.READY`.
        """
        return False

    def stop_playback(self) -> bool:
        """Notify GStreamer that it should stop playback.

        Returns :class:`True` if successful, else :class:`False`.
        """
        return False

    def get_current_tags(self):
        """Get the currently playing media's tags.

        If no tags have been found, or nothing is playing this returns an empty
        dictionary. For each set of tags we collect a tags_changed event is
        emitted with the keys of the changed tags. After such calls users may
        call this function to get the updated values.
        """
        return {}

    def wait_for_state_change(self):
        """Block until any pending state changes are complete.

        Should only be used by tests.
        """

    def enable_sync_handler(self) -> None:
        """Enable manual processing of messages from bus.

        Should only be used by tests.
        """
