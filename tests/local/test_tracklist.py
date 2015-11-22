from __future__ import absolute_import, unicode_literals

import random
import unittest

import pykka

from mopidy import core
from mopidy.core import PlaybackState
from mopidy.internal import deprecation
from mopidy.local import actor
from mopidy.models import Playlist, Track

from tests import dummy_audio, path_to_data_dir
from tests.local import generate_song, populate_tracklist


class LocalTracklistProviderTest(unittest.TestCase):
    config = {
        'core': {
            'data_dir': path_to_data_dir(''),
            'max_tracklist_length': 10000
        },
        'local': {
            'media_dir': path_to_data_dir(''),
            'playlists_dir': b'',
            'library': 'json',
        }
    }
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]

    def run(self, result=None):
        with deprecation.ignore('core.tracklist.add:tracks_arg'):
            return super(LocalTracklistProviderTest, self).run(result)

    def setUp(self):  # noqa: N802
        self.audio = dummy_audio.create_proxy()
        self.backend = actor.LocalBackend.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core.start(audio=self.audio,
                                    backends=[self.backend],
                                    config=self.config).proxy()
        self.controller = self.core.tracklist
        self.playback = self.core.playback

        assert len(self.tracks) == 3, 'Need three tracks to run tests.'

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def assert_state_is(self, state):
        self.assertEqual(self.playback.get_state().get(), state)

    def assert_current_track_is(self, track):
        self.assertEqual(self.playback.get_current_track().get(), track)

    def test_length(self):
        self.assertEqual(0, len(self.controller.get_tl_tracks().get()))
        self.assertEqual(0, self.controller.get_length().get())
        self.controller.add(self.tracks)
        self.assertEqual(3, len(self.controller.get_tl_tracks().get()))
        self.assertEqual(3, self.controller.get_length().get())

    def test_add(self):
        for track in self.tracks:
            added = self.controller.add([track]).get()
            tracks = self.controller.get_tracks().get()
            tl_tracks = self.controller.get_tl_tracks().get()

            self.assertEqual(track, tracks[-1])
            self.assertEqual(added[0], tl_tracks[-1])
            self.assertEqual(track, added[0].track)

    def test_add_at_position(self):
        for track in self.tracks[:-1]:
            added = self.controller.add([track], 0).get()
            tracks = self.controller.get_tracks().get()
            tl_tracks = self.controller.get_tl_tracks().get()

            self.assertEqual(track, tracks[0])
            self.assertEqual(added[0], tl_tracks[0])
            self.assertEqual(track, added[0].track)

    @populate_tracklist
    def test_add_at_position_outside_of_playlist(self):
        for track in self.tracks:
            added = self.controller.add([track], len(self.tracks) + 2).get()
            tracks = self.controller.get_tracks().get()
            tl_tracks = self.controller.get_tl_tracks().get()

            self.assertEqual(track, tracks[-1])
            self.assertEqual(added[0], tl_tracks[-1])
            self.assertEqual(track, added[0].track)

    @populate_tracklist
    def test_filter_by_tlid(self):
        tl_track = self.controller.get_tl_tracks().get()[1]
        result = self.controller.filter({'tlid': [tl_track.tlid]}).get()
        self.assertEqual([tl_track], result)

    @populate_tracklist
    def test_filter_by_uri(self):
        tl_track = self.controller.get_tl_tracks().get()[1]
        result = self.controller.filter({'uri': [tl_track.track.uri]}).get()
        self.assertEqual([tl_track], result)

    @populate_tracklist
    def test_filter_by_uri_returns_nothing_for_invalid_uri(self):
        self.assertEqual([], self.controller.filter({'uri': ['foobar']}).get())

    def test_filter_by_uri_returns_single_match(self):
        t = Track(uri='a')
        self.controller.add([Track(uri='z'), t, Track(uri='y')])

        result = self.controller.filter({'uri': ['a']}).get()
        self.assertEqual(t, result[0].track)

    def test_filter_by_uri_returns_multiple_matches(self):
        track = Track(uri='a')
        self.controller.add([Track(uri='z'), track, track])
        tl_tracks = self.controller.filter({'uri': ['a']}).get()
        self.assertEqual(track, tl_tracks[0].track)
        self.assertEqual(track, tl_tracks[1].track)

    def test_filter_by_uri_returns_nothing_if_no_match(self):
        self.controller.playlist = Playlist(
            tracks=[Track(uri='z'), Track(uri='y')])
        self.assertEqual([], self.controller.filter({'uri': ['a']}).get())

    def test_filter_by_multiple_criteria_returns_elements_matching_all(self):
        t1 = Track(uri='a', name='x')
        t2 = Track(uri='b', name='x')
        t3 = Track(uri='b', name='y')
        self.controller.add([t1, t2, t3])

        result1 = self.controller.filter({'uri': ['a'], 'name': ['x']}).get()
        self.assertEqual(t1, result1[0].track)

        result2 = self.controller.filter({'uri': ['b'], 'name': ['x']}).get()
        self.assertEqual(t2, result2[0].track)

        result3 = self.controller.filter({'uri': ['b'], 'name': ['y']}).get()
        self.assertEqual(t3, result3[0].track)

    def test_filter_by_criteria_that_is_not_present_in_all_elements(self):
        track1 = Track()
        track2 = Track(uri='b')
        track3 = Track()

        self.controller.add([track1, track2, track3])
        result = self.controller.filter({'uri': ['b']}).get()
        self.assertEqual(track2, result[0].track)

    @populate_tracklist
    def test_clear(self):
        self.controller.clear().get()
        self.assertEqual(len(self.controller.get_tracks().get()), 0)

    def test_clear_empty_playlist(self):
        self.controller.clear().get()
        self.assertEqual(len(self.controller.get_tracks().get()), 0)

    @populate_tracklist
    def test_clear_when_playing(self):
        self.playback.play().get()
        self.assert_state_is(PlaybackState.PLAYING)
        self.controller.clear().get()
        self.assert_state_is(PlaybackState.STOPPED)

    def test_add_appends_to_the_tracklist(self):
        self.controller.add([Track(uri='a'), Track(uri='b')])

        tracks = self.controller.get_tracks().get()
        self.assertEqual(len(tracks), 2)

        self.controller.add([Track(uri='c'), Track(uri='d')])

        tracks = self.controller.get_tracks().get()
        self.assertEqual(len(tracks), 4)
        self.assertEqual(tracks[0].uri, 'a')
        self.assertEqual(tracks[1].uri, 'b')
        self.assertEqual(tracks[2].uri, 'c')
        self.assertEqual(tracks[3].uri, 'd')

    def test_add_does_not_reset_version(self):
        version = self.controller.get_version().get()
        self.controller.add([])
        self.assertEqual(self.controller.get_version().get(), version)

    @populate_tracklist
    def test_add_preserves_playing_state(self):
        self.playback.play().get()

        track = self.playback.get_current_track().get()
        tracks = self.controller.get_tracks().get()
        self.controller.add(tracks[1:2]).get()

        self.assert_state_is(PlaybackState.PLAYING)
        self.assert_current_track_is(track)

    @populate_tracklist
    def test_add_preserves_stopped_state(self):
        tracks = self.controller.get_tracks().get()
        self.controller.add(tracks[1:2]).get()

        self.assert_state_is(PlaybackState.STOPPED)
        self.assert_current_track_is(None)

    @populate_tracklist
    def test_add_returns_the_tl_tracks_that_was_added(self):
        tracks = self.controller.get_tracks().get()

        added = self.controller.add(tracks[1:2]).get()
        tracks = self.controller.get_tracks().get()
        self.assertEqual(added[0].track, tracks[1])

    @populate_tracklist
    def test_move_single(self):
        self.controller.move(0, 0, 2)

        tracks = self.controller.get_tracks().get()
        self.assertEqual(tracks[2], self.tracks[0])

    @populate_tracklist
    def test_move_group(self):
        self.controller.move(0, 2, 1)

        tracks = self.controller.get_tracks().get()
        self.assertEqual(tracks[1], self.tracks[0])
        self.assertEqual(tracks[2], self.tracks[1])

    @populate_tracklist
    def test_moving_track_outside_of_playlist(self):
        num_tracks = len(self.controller.get_tracks().get())
        with self.assertRaises(AssertionError):
            self.controller.move(0, 0, num_tracks + 5).get()

    @populate_tracklist
    def test_move_group_outside_of_playlist(self):
        num_tracks = len(self.controller.get_tracks().get())
        with self.assertRaises(AssertionError):
            self.controller.move(0, 2, num_tracks + 5).get()

    @populate_tracklist
    def test_move_group_out_of_range(self):
        num_tracks = len(self.controller.get_tracks().get())
        with self.assertRaises(AssertionError):
            self.controller.move(num_tracks + 2, num_tracks + 3, 0).get()

    @populate_tracklist
    def test_move_group_invalid_group(self):
        with self.assertRaises(AssertionError):
            self.controller.move(2, 1, 0).get()

    def test_tracks_attribute_is_immutable(self):
        tracks1 = self.controller.tracks.get()
        tracks2 = self.controller.tracks.get()
        self.assertNotEqual(id(tracks1), id(tracks2))

    @populate_tracklist
    def test_remove(self):
        track1 = self.controller.get_tracks().get()[1]
        track2 = self.controller.get_tracks().get()[2]
        version = self.controller.get_version().get()
        self.controller.remove({'uri': [track1.uri]})
        self.assertLess(version, self.controller.get_version().get())
        self.assertNotIn(track1, self.controller.get_tracks().get())
        self.assertEqual(track2, self.controller.get_tracks().get()[1])

    @populate_tracklist
    def test_removing_track_that_does_not_exist_does_nothing(self):
        self.controller.remove({'uri': ['/nonexistant']}).get()

    def test_removing_from_empty_playlist_does_nothing(self):
        self.controller.remove({'uri': ['/nonexistant']}).get()

    @populate_tracklist
    def test_remove_lists(self):
        version = self.controller.get_version().get()
        tracks = self.controller.get_tracks().get()
        track0 = tracks[0]
        track1 = tracks[1]
        track2 = tracks[2]

        self.controller.remove({'uri': [track0.uri, track2.uri]})

        tracks = self.controller.get_tracks().get()
        self.assertLess(version, self.controller.get_version().get())
        self.assertNotIn(track0, tracks)
        self.assertNotIn(track2, tracks)
        self.assertEqual(track1, tracks[0])

    @populate_tracklist
    def test_shuffle(self):
        random.seed(1)
        self.controller.shuffle()

        shuffled_tracks = self.controller.get_tracks().get()

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_shuffle_subset(self):
        random.seed(1)
        self.controller.shuffle(1, 3)

        shuffled_tracks = self.controller.get_tracks().get()

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_shuffle_invalid_subset(self):
        with self.assertRaises(AssertionError):
            self.controller.shuffle(3, 1).get()

    @populate_tracklist
    def test_shuffle_superset(self):
        num_tracks = len(self.controller.get_tracks().get())
        with self.assertRaises(AssertionError):
            self.controller.shuffle(1, num_tracks + 5).get()

    @populate_tracklist
    def test_shuffle_open_subset(self):
        random.seed(1)
        self.controller.shuffle(1)

        shuffled_tracks = self.controller.get_tracks().get()

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_slice_returns_a_subset_of_tracks(self):
        track_slice = self.controller.slice(1, 3).get()
        self.assertEqual(2, len(track_slice))
        self.assertEqual(self.tracks[1], track_slice[0].track)
        self.assertEqual(self.tracks[2], track_slice[1].track)

    @populate_tracklist
    def test_slice_returns_empty_list_if_indexes_outside_tracks_list(self):
        self.assertEqual(0, len(self.controller.slice(7, 8).get()))
        self.assertEqual(0, len(self.controller.slice(-1, 1).get()))

    def test_version_does_not_change_when_adding_nothing(self):
        version = self.controller.get_version().get()
        self.controller.add([])
        self.assertEqual(version, self.controller.get_version().get())

    def test_version_increases_when_adding_something(self):
        version = self.controller.get_version().get()
        self.controller.add([Track()])
        self.assertLess(version, self.controller.get_version().get())
