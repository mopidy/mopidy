from __future__ import absolute_import, unicode_literals

from mopidy.internal import validation
from mopidy.models import Ref, TlTrack, fields
from mopidy.models.immutable import ValidatedImmutableObject


class HistoryTrack(ValidatedImmutableObject):
    """
    A history track. Wraps a :class:`Ref` and its timestamp.

    :param timestamp: the timestamp
    :type timestamp: int
    :param track: the track reference
    :type track: :class:`Ref`
    """

    # The timestamp. Read-only.
    timestamp = fields.Integer()

    # The track reference. Read-only.
    track = fields.Field(type=Ref)


class HistoryState(ValidatedImmutableObject):
    """
    State of the history controller.
    Internally used for save/load state.

    :param history: the track history
    :type history: list of :class:`HistoryTrack`
    """

    # The tracks. Read-only.
    history = fields.Collection(type=HistoryTrack, container=tuple)


class MixerState(ValidatedImmutableObject):
    """
    State of the mixer controller.
    Internally used for save/load state.

    :param volume: the volume
    :type volume: int
    :param mute: the mute state
    :type mute: int
    """

    # The volume. Read-only.
    volume = fields.Integer(min=0, max=100)

    # The mute state. Read-only.
    mute = fields.Boolean(default=False)


class PlaybackState(ValidatedImmutableObject):
    """
    State of the playback controller.
    Internally used for save/load state.

    :param tlid: current track tlid
    :type tlid: int
    :param time_position: play position
    :type time_position: int
    :param state: playback state
    :type state: :class:`validation.PLAYBACK_STATES`
    """

    # The tlid of current playing track. Read-only.
    tlid = fields.Integer(min=1)

    # The playback position. Read-only.
    time_position = fields.Integer(min=0)

    # The playback state. Read-only.
    state = fields.Field(choices=validation.PLAYBACK_STATES)


class TracklistState(ValidatedImmutableObject):

    """
    State of the tracklist controller.
    Internally used for save/load state.

    :param repeat: the repeat mode
    :type repeat: bool
    :param consume: the consume mode
    :type consume: bool
    :param random: the random mode
    :type random: bool
    :param single: the single mode
    :type single: bool
    :param next_tlid: the id for the next added track
    :type next_tlid: int
    :param tl_tracks: the list of tracks
    :type tl_tracks: list of :class:`TlTrack`
    """

    # The repeat mode. Read-only.
    repeat = fields.Boolean()

    # The consume mode. Read-only.
    consume = fields.Boolean()

    # The random mode. Read-only.
    random = fields.Boolean()

    # The single mode. Read-only.
    single = fields.Boolean()

    # The id of the track to play. Read-only.
    next_tlid = fields.Integer(min=0)

    # The list of tracks. Read-only.
    tl_tracks = fields.Collection(type=TlTrack, container=tuple)


class CoreState(ValidatedImmutableObject):

    """
    State of all Core controller.
    Internally used for save/load state.

    :param history: State of the history controller
    :type history: :class:`HistorState`
    :param mixer: State of the mixer controller
    :type mixer: :class:`MixerState`
    :param playback: State of the playback controller
    :type playback: :class:`PlaybackState`
    :param tracklist: State of the tracklist controller
    :type tracklist: :class:`TracklistState`
    """

    # State of the history controller.
    history = fields.Field(type=HistoryState)

    # State of the mixer controller.
    mixer = fields.Field(type=MixerState)

    # State of the playback controller.
    playback = fields.Field(type=PlaybackState)

    # State of the tracklist controller.
    tracklist = fields.Field(type=TracklistState)
