from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pykka
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

from mopidy.types import DurationMs, PlaybackState

if TYPE_CHECKING:
    from mopidy.internal.gi import Gst


class Audio:
    """Audio output API.

    There is only a single implementation of this API, using `GStreamer
    <https://gstreamer.freedesktop.org/>`_.

    The primary motivation for defining this API separate from the
    implementation is to make it a bit easier to mock the audio layer in tests.
    If we ever add more implementations, changes to this API will probably be
    necessary.
    """

    #: The GStreamer state mapped to :class:`mopidy.types.PlaybackState`
    state: PlaybackState = PlaybackState.STOPPED

    def set_uri(
        self,
        uri: str,
        live_stream: bool = False,
        download: bool = False,
    ) -> None:
        """Set URI of audio to be played.

        You *MUST* call :meth:`prepare_change` before calling this method.

        :param uri: the URI to play
        :param live_stream: disables buffering, reducing latency for stream,
            and discarding data when paused
        :param download: enables "download" buffering mode
        """
        raise NotImplementedError

    def set_source_setup_callback(
        self,
        callback: Callable[[Gst.Element], None],
    ) -> None:
        """Configure audio to use a source-setup callback.

        This should be used to modify source-specific properties such as login
        details.

        :param callback: Callback to run when we setup the source.
        """
        raise NotImplementedError

    def set_about_to_finish_callback(
        self,
        callback: Callable[[], None],
    ) -> None:
        """Configure audio to use an about-to-finish callback.

        This should be used to achieve gapless playback. For this to work the
        callback *MUST* call :meth:`set_uri` with the new URI to play and
        block until this call has been made. :meth:`prepare_change` is not
        needed before :meth:`set_uri` in this one special case.

        :param callback: Callback to run when we need the next URI.
        """
        raise NotImplementedError

    def get_position(self) -> DurationMs:
        """Get position in milliseconds."""
        raise NotImplementedError

    def set_position(self, position: DurationMs) -> bool:
        """Set position in milliseconds.

        :param position: the position in milliseconds
        """
        raise NotImplementedError

    def start_playback(self) -> bool:
        """Start playback.

        Returns :class:`True` if successful, else :class:`False`.
        """
        raise NotImplementedError

    def pause_playback(self) -> bool:
        """Pause playback.

        Returns :class:`True` if successful, else :class:`False`.
        """
        raise NotImplementedError

    def prepare_change(self) -> bool:
        """Notify audio layer that we are about to change playback state.

        This function *MUST* be called before changing URIs or doing
        changes like updating data that is being pushed.
        """
        raise NotImplementedError

    def stop_playback(self) -> bool:
        """Stop playback.

        Returns :class:`True` if successful, else :class:`False`.
        """
        raise NotImplementedError

    def get_current_tags(self) -> dict[str, list[Any]]:
        """Get the currently playing media's tags.

        If no tags have been found, or nothing is playing this returns an empty
        dictionary. For each set of tags we collect a `tags_changed` event is
        emitted with the keys of the changed tags. After such calls users may
        call this function to get the updated values.
        """
        raise NotImplementedError

    def testing_gst__wait_for_state_change(self) -> None:
        """Block until any pending playback state changes are complete.

        Not part of the API. Only for testing of GstAudio.
        """

    def testing_gst__enable_sync_handler(self) -> None:
        """Enable manual processing of messages from bus.

        Not part of the API. Only for testing of GstAudio.
        """


class AudioActor(pykka.ThreadingActor, Audio):
    pass


class AudioProxy(ActorMemberMixin, pykka.ActorProxy[AudioActor]):
    """Audio layer wrapped in a Pykka actor proxy."""

    state = proxy_field(Audio.state)
    set_uri = proxy_method(Audio.set_uri)
    set_source_setup_callback = proxy_method(Audio.set_source_setup_callback)
    set_about_to_finish_callback = proxy_method(Audio.set_about_to_finish_callback)
    get_position = proxy_method(Audio.get_position)
    set_position = proxy_method(Audio.set_position)
    start_playback = proxy_method(Audio.start_playback)
    pause_playback = proxy_method(Audio.pause_playback)
    prepare_change = proxy_method(Audio.prepare_change)
    stop_playback = proxy_method(Audio.stop_playback)
    get_current_tags = proxy_method(Audio.get_current_tags)
    testing_gst__wait_for_state_change = proxy_method(
        Audio.testing_gst__wait_for_state_change
    )
    testing_gst__enable_sync_handler = proxy_method(
        Audio.testing_gst__enable_sync_handler
    )
