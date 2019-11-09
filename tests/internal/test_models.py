import json
import unittest

from mopidy.internal.models import (
    HistoryState,
    HistoryTrack,
    MixerState,
    PlaybackState,
    TracklistState,
)
from mopidy.models import (
    ModelJSONEncoder,
    Ref,
    TlTrack,
    Track,
    model_json_decoder,
)


class HistoryTrackTest(unittest.TestCase):
    def test_track(self):
        track = Ref.track()
        result = HistoryTrack(track=track)
        assert result.track == track
        with self.assertRaises(AttributeError):
            result.track = None

    def test_timestamp(self):
        timestamp = 1234
        result = HistoryTrack(timestamp=timestamp)
        assert result.timestamp == timestamp
        with self.assertRaises(AttributeError):
            result.timestamp = None

    def test_to_json_and_back(self):
        result = HistoryTrack(track=Ref.track(), timestamp=1234)
        serialized = json.dumps(result, cls=ModelJSONEncoder)
        deserialized = json.loads(serialized, object_hook=model_json_decoder)
        assert result == deserialized


class HistoryStateTest(unittest.TestCase):
    def test_history_list(self):
        history = (HistoryTrack(), HistoryTrack())
        result = HistoryState(history=history)
        assert result.history == history
        with self.assertRaises(AttributeError):
            result.history = None

    def test_history_string_fail(self):
        history = "not_a_valid_history"
        with self.assertRaises(TypeError):
            HistoryState(history=history)

    def test_to_json_and_back(self):
        result = HistoryState(history=(HistoryTrack(), HistoryTrack()))
        serialized = json.dumps(result, cls=ModelJSONEncoder)
        deserialized = json.loads(serialized, object_hook=model_json_decoder)
        assert result == deserialized


class MixerStateTest(unittest.TestCase):
    def test_volume(self):
        volume = 37
        result = MixerState(volume=volume)
        assert result.volume == volume
        with self.assertRaises(AttributeError):
            result.volume = None

    def test_volume_invalid(self):
        volume = 105
        with self.assertRaises(ValueError):
            MixerState(volume=volume)

    def test_mute_false(self):
        mute = False
        result = MixerState(mute=mute)
        assert result.mute == mute
        with self.assertRaises(AttributeError):
            result.mute = None

    def test_mute_true(self):
        mute = True
        result = MixerState(mute=mute)
        assert result.mute == mute
        with self.assertRaises(AttributeError):
            result.mute = False

    def test_mute_default(self):
        result = MixerState()
        assert result.mute is False

    def test_to_json_and_back(self):
        result = MixerState(volume=77)
        serialized = json.dumps(result, cls=ModelJSONEncoder)
        deserialized = json.loads(serialized, object_hook=model_json_decoder)
        assert result == deserialized


class PlaybackStateTest(unittest.TestCase):
    def test_position(self):
        time_position = 123456
        result = PlaybackState(time_position=time_position)
        assert result.time_position == time_position
        with self.assertRaises(AttributeError):
            result.time_position = None

    def test_position_invalid(self):
        time_position = -1
        with self.assertRaises(ValueError):
            PlaybackState(time_position=time_position)

    def test_tl_track(self):
        tlid = 42
        result = PlaybackState(tlid=tlid)
        assert result.tlid == tlid
        with self.assertRaises(AttributeError):
            result.tlid = None

    def test_tl_track_none(self):
        tlid = None
        result = PlaybackState(tlid=tlid)
        assert result.tlid == tlid
        with self.assertRaises(AttributeError):
            result.tl_track = None

    def test_tl_track_invalid(self):
        tl_track = Track()
        with self.assertRaises(TypeError):
            PlaybackState(tlid=tl_track)

    def test_state(self):
        state = "playing"
        result = PlaybackState(state=state)
        assert result.state == state
        with self.assertRaises(AttributeError):
            result.state = None

    def test_state_invalid(self):
        state = "not_a_state"
        with self.assertRaises(TypeError):
            PlaybackState(state=state)

    def test_to_json_and_back(self):
        result = PlaybackState(state="playing", tlid=4321)
        serialized = json.dumps(result, cls=ModelJSONEncoder)
        deserialized = json.loads(serialized, object_hook=model_json_decoder)
        assert result == deserialized


class TracklistStateTest(unittest.TestCase):
    def test_repeat_true(self):
        repeat = True
        result = TracklistState(repeat=repeat)
        assert result.repeat == repeat
        with self.assertRaises(AttributeError):
            result.repeat = None

    def test_repeat_false(self):
        repeat = False
        result = TracklistState(repeat=repeat)
        assert result.repeat == repeat
        with self.assertRaises(AttributeError):
            result.repeat = None

    def test_repeat_invalid(self):
        repeat = 33
        with self.assertRaises(TypeError):
            TracklistState(repeat=repeat)

    def test_consume_true(self):
        val = True
        result = TracklistState(consume=val)
        assert result.consume == val
        with self.assertRaises(AttributeError):
            result.repeat = None

    def test_random_true(self):
        val = True
        result = TracklistState(random=val)
        assert result.random == val
        with self.assertRaises(AttributeError):
            result.random = None

    def test_single_true(self):
        val = True
        result = TracklistState(single=val)
        assert result.single == val
        with self.assertRaises(AttributeError):
            result.single = None

    def test_next_tlid(self):
        val = 654
        result = TracklistState(next_tlid=val)
        assert result.next_tlid == val
        with self.assertRaises(AttributeError):
            result.next_tlid = None

    def test_next_tlid_invalid(self):
        val = -1
        with self.assertRaises(ValueError):
            TracklistState(next_tlid=val)

    def test_tracks(self):
        tracks = (TlTrack(), TlTrack())
        result = TracklistState(tl_tracks=tracks)
        assert result.tl_tracks == tracks
        with self.assertRaises(AttributeError):
            result.tl_tracks = None

    def test_tracks_invalid(self):
        tracks = (Track(), Track())
        with self.assertRaises(TypeError):
            TracklistState(tl_tracks=tracks)

    def test_to_json_and_back(self):
        result = TracklistState(tl_tracks=(TlTrack(), TlTrack()), next_tlid=4)
        serialized = json.dumps(result, cls=ModelJSONEncoder)
        deserialized = json.loads(serialized, object_hook=model_json_decoder)
        assert result == deserialized
