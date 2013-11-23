from __future__ import unicode_literals

import random
import unittest

import pykka

from mopidy import audio, core
from mopidy.backends.local import actor
from mopidy.core import PlaybackState
from mopidy.models import Playlist, TlTrack, Track

from tests import path_to_data_dir
from tests.backends.local import generate_song, populate_tracklist


class LocalTracklistProviderTest(unittest.TestCase):
    config = {
        'local': {
            'media_dir': path_to_data_dir(''),
            'playlists_dir': b'',
            'tag_cache_file': path_to_data_dir('empty_tag_cache'),
        }
    }
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]

    def setUp(self):
        self.audio = audio.DummyAudio.start().proxy()
        self.backend = actor.LocalBackend.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core(audio=self.audio, backends=[self.backend])
        self.controller = self.core.tracklist
        self.playback = self.core.playback

        assert len(self.tracks) == 3, 'Need three tracks to run tests.'

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_length(self):
        self.assertEqual(0, len(self.controller.tl_tracks))
        self.assertEqual(0, self.controller.length)
        self.controller.add(self.tracks)
        self.assertEqual(3, len(self.controller.tl_tracks))
        self.assertEqual(3, self.controller.length)

    def test_add(self):
        for track in self.tracks:
            tl_tracks = self.controller.add([track])
            self.assertEqual(track, self.controller.tracks[-1])
            self.assertEqual(tl_tracks[0], self.controller.tl_tracks[-1])
            self.assertEqual(track, tl_tracks[0].track)

    def test_add_at_position(self):
        for track in self.tracks[:-1]:
            tl_tracks = self.controller.add([track], 0)
            self.assertEqual(track, self.controller.tracks[0])
            self.assertEqual(tl_tracks[0], self.controller.tl_tracks[0])
            self.assertEqual(track, tl_tracks[0].track)

    @populate_tracklist
    def test_add_at_position_outside_of_playlist(self):
        for track in self.tracks:
            tl_tracks = self.controller.add([track], len(self.tracks) + 2)
            self.assertEqual(track, self.controller.tracks[-1])
            self.assertEqual(tl_tracks[0], self.controller.tl_tracks[-1])
            self.assertEqual(track, tl_tracks[0].track)

    @populate_tracklist
    def test_filter_by_tlid(self):
        tl_track = self.controller.tl_tracks[1]
        self.assertEqual(
            [tl_track], self.controller.filter(tlid=[tl_track.tlid]))

    @populate_tracklist
    def test_filter_by_uri(self):
        tl_track = self.controller.tl_tracks[1]
        self.assertEqual(
            [tl_track], self.controller.filter(uri=[tl_track.track.uri]))

    @populate_tracklist
    def test_filter_by_uri_returns_nothing_for_invalid_uri(self):
        self.assertEqual([], self.controller.filter(uri=['foobar']))

    def test_filter_by_uri_returns_single_match(self):
        track = Track(uri='a')
        self.controller.add([Track(uri='z'), track, Track(uri='y')])
        self.assertEqual(track, self.controller.filter(uri=['a'])[0].track)

    def test_filter_by_uri_returns_multiple_matches(self):
        track = Track(uri='a')
        self.controller.add([Track(uri='z'), track, track])
        tl_tracks = self.controller.filter(uri=['a'])
        self.assertEqual(track, tl_tracks[0].track)
        self.assertEqual(track, tl_tracks[1].track)

    def test_filter_by_uri_returns_nothing_if_no_match(self):
        self.controller.playlist = Playlist(
            tracks=[Track(uri=['z']), Track(uri=['y'])])
        self.assertEqual([], self.controller.filter(uri=['a']))

    def test_filter_by_multiple_criteria_returns_elements_matching_all(self):
        track1 = Track(uri='a', name='x')
        track2 = Track(uri='b', name='x')
        track3 = Track(uri='b', name='y')
        self.controller.add([track1, track2, track3])
        self.assertEqual(
            track1, self.controller.filter(uri=['a'], name=['x'])[0].track)
        self.assertEqual(
            track2, self.controller.filter(uri=['b'], name=['x'])[0].track)
        self.assertEqual(
            track3, self.controller.filter(uri=['b'], name=['y'])[0].track)

    def test_filter_by_criteria_that_is_not_present_in_all_elements(self):
        track1 = Track()
        track2 = Track(uri='b')
        track3 = Track()
        self.controller.add([track1, track2, track3])
        self.assertEqual(track2, self.controller.filter(uri=['b'])[0].track)

    @populate_tracklist
    def test_clear(self):
        self.controller.clear()
        self.assertEqual(len(self.controller.tracks), 0)

    def test_clear_empty_playlist(self):
        self.controller.clear()
        self.assertEqual(len(self.controller.tracks), 0)

    @populate_tracklist
    def test_clear_when_playing(self):
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.controller.clear()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    def test_add_appends_to_the_tracklist(self):
        self.controller.add([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.controller.tracks), 2)
        self.controller.add([Track(uri='c'), Track(uri='d')])
        self.assertEqual(len(self.controller.tracks), 4)
        self.assertEqual(self.controller.tracks[0].uri, 'a')
        self.assertEqual(self.controller.tracks[1].uri, 'b')
        self.assertEqual(self.controller.tracks[2].uri, 'c')
        self.assertEqual(self.controller.tracks[3].uri, 'd')

    def test_add_does_not_reset_version(self):
        version = self.controller.version
        self.controller.add([])
        self.assertEqual(self.controller.version, version)

    @populate_tracklist
    def test_add_preserves_playing_state(self):
        self.playback.play()
        track = self.playback.current_track
        self.controller.add(self.controller.tracks[1:2])
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(self.playback.current_track, track)

    @populate_tracklist
    def test_add_preserves_stopped_state(self):
        self.controller.add(self.controller.tracks[1:2])
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_tracklist
    def test_add_returns_the_tl_tracks_that_was_added(self):
        tl_tracks = self.controller.add(self.controller.tracks[1:2])
        self.assertEqual(tl_tracks[0].track, self.controller.tracks[1])

    def test_index_returns_index_of_track(self):
        tl_tracks = self.controller.add(self.tracks)
        self.assertEqual(0, self.controller.index(tl_tracks[0]))
        self.assertEqual(1, self.controller.index(tl_tracks[1]))
        self.assertEqual(2, self.controller.index(tl_tracks[2]))

    def test_index_returns_none_if_item_not_found(self):
        tl_track = TlTrack(0, Track())
        self.assertEqual(self.controller.index(tl_track), None)

    @populate_tracklist
    def test_move_single(self):
        self.controller.move(0, 0, 2)

        tracks = self.controller.tracks
        self.assertEqual(tracks[2], self.tracks[0])

    @populate_tracklist
    def test_move_group(self):
        self.controller.move(0, 2, 1)

        tracks = self.controller.tracks
        self.assertEqual(tracks[1], self.tracks[0])
        self.assertEqual(tracks[2], self.tracks[1])

    @populate_tracklist
    def test_moving_track_outside_of_playlist(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.move(0, 0, tracks + 5)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_move_group_outside_of_playlist(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.move(0, 2, tracks + 5)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_move_group_out_of_range(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.move(tracks + 2, tracks + 3, 0)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_move_group_invalid_group(self):
        test = lambda: self.controller.move(2, 1, 0)
        self.assertRaises(AssertionError, test)

    def test_tracks_attribute_is_immutable(self):
        tracks1 = self.controller.tracks
        tracks2 = self.controller.tracks
        self.assertNotEqual(id(tracks1), id(tracks2))

    @populate_tracklist
    def test_remove(self):
        track1 = self.controller.tracks[1]
        track2 = self.controller.tracks[2]
        version = self.controller.version
        self.controller.remove(uri=[track1.uri])
        self.assertLess(version, self.controller.version)
        self.assertNotIn(track1, self.controller.tracks)
        self.assertEqual(track2, self.controller.tracks[1])

    @populate_tracklist
    def test_removing_track_that_does_not_exist_does_nothing(self):
        self.controller.remove(uri=['/nonexistant'])

    def test_removing_from_empty_playlist_does_nothing(self):
        self.controller.remove(uri=['/nonexistant'])

    @populate_tracklist
    def test_remove_lists(self):
        track0 = self.controller.tracks[0]
        track1 = self.controller.tracks[1]
        track2 = self.controller.tracks[2]
        version = self.controller.version
        self.controller.remove(uri=[track0.uri, track2.uri])
        self.assertLess(version, self.controller.version)
        self.assertNotIn(track0, self.controller.tracks)
        self.assertNotIn(track2, self.controller.tracks)
        self.assertEqual(track1, self.controller.tracks[0])

    @populate_tracklist
    def test_shuffle(self):
        random.seed(1)
        self.controller.shuffle()

        shuffled_tracks = self.controller.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_shuffle_subset(self):
        random.seed(1)
        self.controller.shuffle(1, 3)

        shuffled_tracks = self.controller.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_shuffle_invalid_subset(self):
        test = lambda: self.controller.shuffle(3, 1)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_shuffle_superset(self):
        tracks = len(self.controller.tracks)
        test = lambda: self.controller.shuffle(1, tracks + 5)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_shuffle_open_subset(self):
        random.seed(1)
        self.controller.shuffle(1)

        shuffled_tracks = self.controller.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_slice_returns_a_subset_of_tracks(self):
        track_slice = self.controller.slice(1, 3)
        self.assertEqual(2, len(track_slice))
        self.assertEqual(self.tracks[1], track_slice[0].track)
        self.assertEqual(self.tracks[2], track_slice[1].track)

    @populate_tracklist
    def test_slice_returns_empty_list_if_indexes_outside_tracks_list(self):
        self.assertEqual(0, len(self.controller.slice(7, 8)))
        self.assertEqual(0, len(self.controller.slice(-1, 1)))

    def test_version_does_not_change_when_adding_nothing(self):
        version = self.controller.version
        self.controller.add([])
        self.assertEquals(version, self.controller.version)

    def test_version_increases_when_adding_something(self):
        version = self.controller.version
        self.controller.add([Track()])
        self.assertLess(version, self.controller.version)
