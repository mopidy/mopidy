from __future__ import annotations

from typing import Any, Literal, TypeAlias

from mopidy import listener
from mopidy.audio import PlaybackState
from mopidy.models import Playlist, TlTrack
from mopidy.types import DurationMs, Percentage, Uri

CoreEvent: TypeAlias = Literal[
    "track_playback_paused",
    "track_playback_resumed",
    "track_playback_started",
    "track_playback_ended",
    "playback_state_changed",
    "tracklist_changed",
    "playlists_loaded",
    "playlist_changed",
    "playlist_deleted",
    "options_changed",
    "volume_changed",
    "mute_changed",
    "seeked",
    "stream_title_changed",
]

# A union of all possible data types for the core events. This is used to create
# Pydantic TypeAdapter's to serialize the events to JSON.
CoreEventData: TypeAlias = (
    DurationMs | Percentage | PlaybackState | Playlist | TlTrack | Uri | bool | str
)


class CoreListener(listener.Listener):
    """Marker interface for recipients of events sent by the core actor.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the core actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event: CoreEvent, **kwargs: Any) -> None:
        """Helper to allow calling of core listener events."""
        listener.send(CoreListener, event, **kwargs)

    def on_event(self, event: CoreEvent, **kwargs: CoreEventData) -> None:
        """Called on all events.

        *MAY* be implemented by actor. By default, this method forwards the
        event to the specific event methods.

        :param event: the event name
        :param kwargs: any other arguments to the specific event handlers
        """
        # Just delegate to parent, entry mostly for docs.
        super().on_event(event, **kwargs)

    def track_playback_paused(
        self,
        tl_track: TlTrack,
        time_position: DurationMs,
    ) -> None:
        """Called whenever track playback is paused.

        *MAY* be implemented by actor.

        :param tl_track: the track that was playing when playback paused
        :param time_position: the time position in milliseconds
        """

    def track_playback_resumed(
        self,
        tl_track: TlTrack,
        time_position: DurationMs,
    ) -> None:
        """Called whenever track playback is resumed.

        *MAY* be implemented by actor.

        :param tl_track: the track that was playing when playback resumed
        :param time_position: the time position in milliseconds
        """

    def track_playback_started(self, tl_track: TlTrack) -> None:
        """Called whenever a new track starts playing.

        *MAY* be implemented by actor.

        :param tl_track: the track that just started playing
        """

    def track_playback_ended(
        self,
        tl_track: TlTrack,
        time_position: DurationMs,
    ) -> None:
        """Called whenever playback of a track ends.

        *MAY* be implemented by actor.

        :param tl_track: the track that was played before playback stopped
        :param time_position: the time position in milliseconds
        """

    def playback_state_changed(
        self,
        old_state: PlaybackState,
        new_state: PlaybackState,
    ) -> None:
        """Called whenever playback state is changed.

        *MAY* be implemented by actor.

        :param old_state: the state before the change
        :type old_state: string from :class:`mopidy.core.PlaybackState` field
        :param new_state: the state after the change
        :type new_state: string from :class:`mopidy.core.PlaybackState` field
        """

    def tracklist_changed(self) -> None:
        """Called whenever the tracklist is changed.

        *MAY* be implemented by actor.
        """

    def playlists_loaded(self) -> None:
        """Called when playlists are loaded or refreshed.

        *MAY* be implemented by actor.
        """

    def playlist_changed(self, playlist: Playlist) -> None:
        """Called whenever a playlist is changed.

        *MAY* be implemented by actor.

        :param playlist: the changed playlist
        :type playlist: :class:`mopidy.models.Playlist`
        """

    def playlist_deleted(self, uri: Uri) -> None:
        """Called whenever a playlist is deleted.

        *MAY* be implemented by actor.

        :param uri: the URI of the deleted playlist
        :type uri: string
        """

    def options_changed(self) -> None:
        """Called whenever an option is changed.

        *MAY* be implemented by actor.
        """

    def volume_changed(self, volume: Percentage) -> None:
        """Called whenever the volume is changed.

        *MAY* be implemented by actor.

        :param volume: the new volume in the range [0..100]
        :type volume: int
        """

    def mute_changed(self, mute: bool) -> None:
        """Called whenever the mute state is changed.

        *MAY* be implemented by actor.

        :param mute: the new mute state
        :type mute: boolean
        """

    def seeked(self, time_position: DurationMs) -> None:
        """Called whenever the time position changes by an unexpected amount, e.g.
        at seek to a new time position.

        *MAY* be implemented by actor.

        :param time_position: the position that was seeked to in milliseconds
        :type time_position: int
        """

    def stream_title_changed(self, title: str) -> None:
        """Called whenever the currently playing stream title changes.

        *MAY* be implemented by actor.

        :param title: the new stream title
        :type title: string
        """
