from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from mopidy import listener

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from mopidy.audio import PlaybackState
    from mopidy.types import DurationMs, Uri


AudioEvent: TypeAlias = Literal[
    "position_changed",
    "reached_end_of_stream",
    "state_changed",
    "stream_changed",
    "tags_changed",
]


class AudioListener(listener.Listener):
    """Marker interface for recipients of events sent by the audio actor.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the core actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event: AudioEvent, **kwargs: Any) -> None:
        """Helper to allow calling of audio listener events."""
        listener.send(AudioListener, event, **kwargs)

    def reached_end_of_stream(self) -> None:
        """Called whenever the end of the audio stream is reached.

        *MAY* be implemented by actor.
        """

    def stream_changed(self, uri: Uri) -> None:
        """Called whenever the audio stream changes.

        *MAY* be implemented by actor.

        :param string uri: URI the stream has started playing.
        """

    def position_changed(self, position: DurationMs) -> None:
        """Called whenever the position of the stream changes.

        *MAY* be implemented by actor.

        :param int position: Position in milliseconds.
        """

    def state_changed(
        self,
        old_state: PlaybackState,
        new_state: PlaybackState,
        target_state: Optional[PlaybackState],
    ) -> None:
        """Called after the playback state have changed.

        Will be called for both immediate and async state changes in GStreamer.

        Target state is used to when we should be in the target state, but
        temporarily need to switch to an other state. A typical example of this
        is buffering. When this happens an event with
        `old=PLAYING, new=PAUSED, target=PLAYING` will be emitted. Once we have
        caught up a `old=PAUSED, new=PLAYING, target=None` event will be
        be generated.

        Regular state changes will not have target state set as they are final
        states which should be stable.

        *MAY* be implemented by actor.

        :param old_state: the state before the change
        :type old_state: :class:`mopidy.audio.PlaybackState`
        :param new_state: the state after the change
        :type new_state: :class:`mopidy.audio.PlaybackState`
        :param target_state: the intended state
        :type target_state: :class:`mopidy.audio.PlaybackState`
            or :class:`None` if this is a final state.
        """

    def tags_changed(self, tags: set[str]) -> None:
        """Called whenever the current audio stream's tags change.

        This event signals that some track metadata has been updated. This can
        be metadata such as artists, titles, organization, or details about the
        actual audio such as bit-rates, numbers of channels etc.

        For the available tag keys please refer to GStreamer documentation for
        tags.

        *MAY* be implemented by actor.

        :param tags: The tags that have just been updated.
        :type tags: :class:`set` of strings
        """
