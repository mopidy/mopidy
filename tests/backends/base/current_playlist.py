import mock
import random

from mopidy.models import CpTrack, Playlist, Track
from mopidy.gstreamer import GStreamer

from tests.backends.base import populate_playlist


class CurrentPlaylistControllerTest(object):
    tracks = []

    def setUp(self):
        self.backend = self.backend_class()
        self.backend.gstreamer = mock.Mock(spec=GStreamer)
        self.controller = self.backend.current_playlist
        self.playback = self.backend.playback

        assert len(self.tracks) == 3, 'Need three tracks to run tests.'

    def test_length(self):
        self.assertEqual(0, len(self.controller.cp_tracks))
        self.assertEqual(0, self.controller.length)
        self.controller.append(self.tracks)
        self.assertEqual(3, len(self.controller.cp_tracks))
        self.assertEqual(3, self.controller.length)

    def test_add(self):
        for track in self.tracks:
            cp_track = self.controller.add(track)
            self.assertEqual(track, self.controller.tracks[-1])
            self.assertEqual(cp_track, self.controller.cp_tracks[-1])
            self.assertEqual(track, cp_track.track)

    def test_add_at_position(self):
        for track in self.tracks[:-1]:
            cp_track = self.controller.add(track, 0)
            self.assertEqual(track, self.controller.tracks[0])
            self.assertEqual(cp_track, self.controller.cp_tracks[0])
            self.assertEqual(track, cp_track.track)

    @populate_playlist
    def test_add_at_position_outside_of_playlist(self):
        test = lambda: self.controller.add(self.tracks[0], len(self.tracks)+2)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_get_by_cpid(self):
        cp_track = self.controller.cp_tracks[1]
        self.assertEqual(cp_track, self.controller.get(cpid=cp_track.cpid))

    @populate_playlist
    def test_get_by_uri(self):
        cp_track = self.controller.cp_tracks[1]
        self.assertEqual(cp_track, self.controller.get(uri=cp_track.track.uri))

    @populate_playlist
    def test_get_by_uri_raises_error_for_invalid_uri(self):
        test = lambda: self.controller.get(uri='foobar')
        self.assertRaises(LookupError, test)

    @populate_playlist
    def test_clear(self):
        self.controller.clear()
        self.assertEqual(len(self.controller.tracks), 0)

    def test_clear_empty_playlist(self):
        self.controller.clear()
        self.assertEqual(len(self.controller.tracks), 0)

    @populate_playlist
    def test_clear_when_playing(self):
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.controller.clear()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_get_by_uri_returns_unique_match(self):
        track = Track(uri='a')
        self.controller.append([Track(uri='z'), track, Track(uri='y')])
        self.assertEqual(track, self.controller.get(uri='a')[1])

    def test_get_by_uri_raises_error_if_multiple_matches(self):
        track = Track(uri='a')
        self.controller.append([Track(uri='z'), track, track])
        try:
            self.controller.get(uri='a')
            self.fail(u'Should raise LookupError if multiple matches')
        except LookupError as e:
            self.assertEqual(u'"uri=a" match multiple tracks', e[0])

    def test_get_by_uri_raises_error_if_no_match(self):
        self.controller.playlist = Playlist(
            tracks=[Track(uri='z'), Track(uri='y')])
        try:
            self.controller.get(uri='a')
            self.fail(u'Should raise LookupError if no match')
        except LookupError as e:
            self.assertEqual(u'"uri=a" match no tracks', e[0])

    def test_get_by_multiple_criteria_returns_elements_matching_all(self):
        track1 = Track(uri='a', name='x')
        track2 = Track(uri='b', name='x')
        track3 = Track(uri='b', name='y')
        self.controller.append([track1, track2, track3])
        self.assertEqual(track1, self.controller.get(uri='a', name='x')[1])
        self.assertEqual(track2, self.controller.get(uri='b', name='x')[1])
        self.assertEqual(track3, self.controller.get(uri='b', name='y')[1])

    def test_get_by_criteria_that_is_not_present_in_all_elements(self):
        track1 = Track()
        track2 = Track(uri='b')
        track3 = Track()
        self.controller.append([track1, track2, track3])
        self.assertEqual(track2, self.controller.get(uri='b')[1])

    def test_append_appends_to_the_current_playlist(self):
        self.controller.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.controller.tracks), 2)
        self.controller.append([Track(uri='c'), Track(uri='d')])
        self.assertEqual(len(self.controller.tracks), 4)
        self.assertEqual(self.controller.tracks[0].uri, 'a')
        self.assertEqual(self.controller.tracks[1].uri, 'b')
        self.assertEqual(self.controller.tracks[2].uri, 'c')
        self.assertEqual(self.controller.tracks[3].uri, 'd')

    def test_append_does_not_reset_version(self):
        version = self.controller.version
        self.controller.append([])
        self.assertEqual(self.controller.version, version)

    @populate_playlist
    def test_append_preserves_playing_state(self):
        self.playback.play()
        track = self.playback.current_track
        self.controller.append(self.controller.tracks[1:2])
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, track)

    @populate_playlist
    def test_append_preserves_stopped_state(self):
        self.controller.append(self.controller.tracks[1:2])
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    def test_index_returns_index_of_track(self):
        cp_tracks = []
        for track in self.tracks:
            cp_tracks.append(self.controller.add(track))
        self.assertEquals(0, self.controller.index(cp_tracks[0]))
        self.assertEquals(1, self.controller.index(cp_tracks[1]))
        self.assertEquals(2, self.controller.index(cp_tracks[2]))

    def test_index_raises_value_error_if_item_not_found(self):
        test = lambda: self.controller.index(CpTrack(0, Track()))
        self.assertRaises(ValueError, test)

    @populate_playlist
    def test_move_single(self):
        self.controller.move(0, 0, 2)

        tracks = self.controller.tracks
        self.assertEqual(tracks[2], self.tracks[0])

    @populate_playlist
    def test_move_group(self):
        self.controller.move(0, 2, 1)

        tracks = self.controller.tracks
        self.assertEqual(tracks[1], self.tracks[0])
        self.assertEqual(tracks[2], self.tracks[1])

    @populate_playlist
    def test_moving_track_outside_of_playlist(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.move(0, 0, tracks+5)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_move_group_outside_of_playlist(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.move(0, 2, tracks+5)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_move_group_out_of_range(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.move(tracks+2, tracks+3, 0)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_move_group_invalid_group(self):
        test = lambda: self.controller.move(2, 1, 0)
        self.assertRaises(AssertionError, test)

    def test_tracks_attribute_is_immutable(self):
        tracks1 = self.controller.tracks
        tracks2 = self.controller.tracks
        self.assertNotEqual(id(tracks1), id(tracks2))

    @populate_playlist
    def test_remove(self):
        track1 = self.controller.tracks[1]
        track2 = self.controller.tracks[2]
        version = self.controller.version
        self.controller.remove(uri=track1.uri)
        self.assert_(version < self.controller.version)
        self.assert_(track1 not in self.controller.tracks)
        self.assertEqual(track2, self.controller.tracks[1])

    @populate_playlist
    def test_removing_track_that_does_not_exist(self):
        test = lambda: self.controller.remove(uri='/nonexistant')
        self.assertRaises(LookupError, test)

    def test_removing_from_empty_playlist(self):
        test = lambda: self.controller.remove(uri='/nonexistant')
        self.assertRaises(LookupError, test)

    @populate_playlist
    def test_shuffle(self):
        random.seed(1)
        self.controller.shuffle()

        shuffled_tracks = self.controller.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_playlist
    def test_shuffle_subset(self):
        random.seed(1)
        self.controller.shuffle(1, 3)

        shuffled_tracks = self.controller.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_playlist
    def test_shuffle_invalid_subset(self):
        test = lambda: self.controller.shuffle(3, 1)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_shuffle_superset(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.shuffle(1, tracks+5)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_shuffle_open_subset(self):
        random.seed(1)
        self.controller.shuffle(1)

        shuffled_tracks = self.controller.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_playlist
    def test_slice_returns_a_subset_of_tracks(self):
        track_slice = self.controller.slice(1, 3)
        self.assertEqual(2, len(track_slice))
        self.assertEqual(self.tracks[1], track_slice[0].track)
        self.assertEqual(self.tracks[2], track_slice[1].track)

    @populate_playlist
    def test_slice_returns_empty_list_if_indexes_outside_tracks_list(self):
        self.assertEqual(0, len(self.controller.slice(7, 8)))
        self.assertEqual(0, len(self.controller.slice(-1, 1)))

    def test_version_does_not_change_when_appending_nothing(self):
        version = self.controller.version
        self.controller.append([])
        self.assertEquals(version, self.controller.version)

    def test_version_increases_when_appending_something(self):
        version = self.controller.version
        self.controller.append([Track()])
        self.assert_(version < self.controller.version)
