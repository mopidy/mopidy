import msgspec

from mopidy.models import Ref, TlTrack
from mopidy.models._base import BaseModel
from mopidy.types import DurationMs, NonNegativeInt, Percentage, TracklistId
from mopidy.types import PlaybackState as PlaybackStateEnum


class HistoryTrack(
    BaseModel,
    kw_only=True,
    frozen=True,
):
    """A track that has been played back at a given timestamp.

    Internally used for save/load state.
    """

    # The timestamp when the track was played. Read-only.
    timestamp: NonNegativeInt

    # The track reference. Read-only.
    track: Ref


class HistoryState(
    BaseModel,
    kw_only=True,
    frozen=True,
):
    """
    State of the history controller.

    Internally used for save/load state.
    """

    # The track history. Read-only.
    history: tuple[HistoryTrack, ...] = ()


class MixerState(
    msgspec.Struct,
    kw_only=True,
    frozen=True,
    tag_field="__model__",
    tag="MixerState",
):
    """
    State of the mixer controller.

    Internally used for save/load state.
    """

    # The volume. Read-only.
    volume: Percentage | None = None

    # The mute state. Read-only.
    mute: bool | None = None


class PlaybackState(
    BaseModel,
    kw_only=True,
    frozen=True,
):
    """State of the playback controller.

    Internally used for save/load state.
    """

    # The tlid of current playing track. Read-only.
    tlid: TracklistId | None = None

    # The playback position in milliseconds. Read-only.
    time_position: DurationMs

    # The playback state. Read-only.
    state: PlaybackStateEnum


class TracklistState(
    BaseModel,
    kw_only=True,
    frozen=True,
):
    """State of the tracklist controller.

    Internally used for save/load state.
    """

    # The repeat mode. Read-only.
    repeat: bool

    # The consume mode. Read-only.
    consume: bool

    # The random mode. Read-only.
    random: bool

    # The single mode. Read-only.
    single: bool

    # The id of the track to play. Read-only.
    next_tlid: TracklistId

    # The list of tracks. Read-only.
    tl_tracks: tuple[TlTrack, ...] = ()


class CoreState(
    BaseModel,
    kw_only=True,
    frozen=True,
):
    """State of all Core controllers.

    Internally used for save/load state.
    """

    # State of the history controller.
    history: HistoryState

    # State of the mixer controller.
    mixer: MixerState

    # State of the playback controller.
    playback: PlaybackState

    # State of the tracklist controller.
    tracklist: TracklistState


class StoredState(
    BaseModel,
    kw_only=True,
    frozen=True,
):
    """State of the core that is persisted to disk.

    Internally used for save/load state.
    """

    # The version of the state file. Read-only.
    version: str

    # The state of the core. Read-only.
    state: CoreState
