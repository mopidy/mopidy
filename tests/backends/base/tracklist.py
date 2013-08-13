from __future__ import unicode_literals

import random

import pykka

from mopidy import audio, core
from mopidy.core import PlaybackState
from mopidy.models import TlTrack, Playlist, Track

from tests.backends.base import populate_tracklist


class TracklistControllerTest(object):
    tracks = []
    config = {}

    def setUp(self):
        self.audio = audio.DummyAudio.start().proxy()
        self.backend = self.backend_class.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core(audio=self.audio, backends=[self.backend])
        self.tracklist = self.core.tracklist
        self.playback = self.core.playback

        assert len(self.tracks) == 3, 'Need three tracks to run tests.'

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_length(self):
        self.assertEqual(0, len(self.tracklist.tl_tracks))
        self.assertEqual(0, self.tracklist.length)
        self.tracklist.add(self.tracks)
        self.assertEqual(3, len(self.tracklist.tl_tracks))
        self.assertEqual(3, self.tracklist.length)

    def test_add(self):
        for track in self.tracks:
            tl_tracks = self.tracklist.add([track])
            self.assertEqual(track, self.tracklist.tracks[-1])
            self.assertEqual(tl_tracks[0], self.tracklist.tl_tracks[-1])
            self.assertEqual(track, tl_tracks[0].track)

    def test_add_at_position(self):
        for track in self.tracks[:-1]:
            tl_tracks = self.tracklist.add([track], 0)
            self.assertEqual(track, self.tracklist.tracks[0])
            self.assertEqual(tl_tracks[0], self.tracklist.tl_tracks[0])
            self.assertEqual(track, tl_tracks[0].track)

    @populate_tracklist
    def test_add_at_position_outside_of_playlist(self):
        for track in self.tracks:
            tl_tracks = self.tracklist.add([track], len(self.tracks) + 2)
            self.assertEqual(track, self.tracklist.tracks[-1])
            self.assertEqual(tl_tracks[0], self.tracklist.tl_tracks[-1])
            self.assertEqual(track, tl_tracks[0].track)

    @populate_tracklist
    def test_filter_by_tlid(self):
        tl_track = self.tracklist.tl_tracks[1]
        self.assertEqual(
            [tl_track], self.tracklist.filter(tlid=tl_track.tlid))

    @populate_tracklist
    def test_filter_by_uri(self):
        tl_track = self.tracklist.tl_tracks[1]
        self.assertEqual(
            [tl_track], self.tracklist.filter(uri=tl_track.track.uri))

    @populate_tracklist
    def test_filter_by_uri_returns_nothing_for_invalid_uri(self):
        self.assertEqual([], self.tracklist.filter(uri='foobar'))

    def test_filter_by_uri_returns_single_match(self):
        track = Track(uri='a')
        self.tracklist.add([Track(uri='z'), track, Track(uri='y')])
        self.assertEqual(track, self.tracklist.filter(uri='a')[0].track)

    def test_filter_by_uri_returns_multiple_matches(self):
        track = Track(uri='a')
        self.tracklist.add([Track(uri='z'), track, track])
        tl_tracks = self.tracklist.filter(uri='a')
        self.assertEqual(track, tl_tracks[0].track)
        self.assertEqual(track, tl_tracks[1].track)

    def test_filter_by_uri_returns_nothing_if_no_match(self):
        self.tracklist.playlist = Playlist(
            tracks=[Track(uri='z'), Track(uri='y')])
        self.assertEqual([], self.tracklist.filter(uri='a'))

    def test_filter_by_multiple_criteria_returns_elements_matching_all(self):
        track1 = Track(uri='a', name='x')
        track2 = Track(uri='b', name='x')
        track3 = Track(uri='b', name='y')
        self.tracklist.add([track1, track2, track3])
        self.assertEqual(
            track1, self.tracklist.filter(uri='a', name='x')[0].track)
        self.assertEqual(
            track2, self.tracklist.filter(uri='b', name='x')[0].track)
        self.assertEqual(
            track3, self.tracklist.filter(uri='b', name='y')[0].track)

    def test_filter_by_criteria_that_is_not_present_in_all_elements(self):
        track1 = Track()
        track2 = Track(uri='b')
        track3 = Track()
        self.tracklist.add([track1, track2, track3])
        self.assertEqual(track2, self.tracklist.filter(uri='b')[0].track)

    @populate_tracklist
    def test_clear(self):
        self.tracklist.clear()
        self.assertEqual(len(self.tracklist.tracks), 0)

    def test_clear_empty_playlist(self):
        self.tracklist.clear()
        self.assertEqual(len(self.tracklist.tracks), 0)

    @populate_tracklist
    def test_clear_when_playing(self):
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.tracklist.clear()
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)

    @populate_tracklist
    def test_next_track_before_play(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[0])

    @populate_tracklist
    def test_next_track_during_play(self):
        self.playback.play()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[1])

    @populate_tracklist
    def test_next_track_after_previous(self):
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[1])

    def test_next_track_empty_playlist(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track), None)

    @populate_tracklist
    def test_next_track_at_end_of_playlist(self):
        self.playback.play()
        for _ in self.tracklist.tl_tracks[1:]:
            self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track), None)

    @populate_tracklist
    def test_next_track_at_end_of_playlist_with_repeat(self):
        self.tracklist.repeat = True
        self.playback.play()
        for _ in self.tracks[1:]:
            self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[0])

    @populate_tracklist
    def test_next_track_with_random(self):
        random.seed(1)
        self.tracklist.random = True
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[2])

    @populate_tracklist
    def test_next_with_consume(self):
        self.tracklist.consume = True
        self.playback.play()
        self.playback.next()
        self.assertIn(self.tracks[0], self.tracklist.tracks)

    @populate_tracklist
    def test_next_with_single_and_repeat(self):
        self.tracklist.single = True
        self.tracklist.repeat = True
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_next_with_random(self):
        # FIXME feels very fragile
        random.seed(1)
        self.tracklist.random = True
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_next_track_with_random_after_append_playlist(self):
        random.seed(1)
        self.tracklist.random = True
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[2])
        self.tracklist.add(self.tracks[:1])
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[1])

    @populate_tracklist
    def test_end_of_track_track_before_play(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[0])

    @populate_tracklist
    def test_end_of_track_track_during_play(self):
        self.playback.play()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[1])

    @populate_tracklist
    def test_end_of_track_track_after_previous(self):
        self.playback.play()
        self.playback.on_end_of_track()
        self.playback.previous()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[1])

    def test_end_of_track_track_empty_playlist(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track), None)

    @populate_tracklist
    def test_end_of_track_track_at_end_of_playlist(self):
        self.playback.play()
        for _ in self.tracklist.tl_tracks[1:]:
            self.playback.on_end_of_track()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track), None)

    @populate_tracklist
    def test_end_of_track_track_at_end_of_playlist_with_repeat(self):
        self.tracklist.repeat = True
        self.playback.play()
        for _ in self.tracks[1:]:
            self.playback.on_end_of_track()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[0])

    @populate_tracklist
    def test_end_of_track_track_with_random(self):
        random.seed(1)
        self.tracklist.random = True
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[2])

    @populate_tracklist
    def test_end_of_track_with_consume(self):
        self.tracklist.consume = True
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertNotIn(self.tracks[0], self.tracklist.tracks)

    @populate_tracklist
    def test_end_of_track_with_random(self):
        # FIXME feels very fragile
        random.seed(1)
        self.tracklist.random = True
        self.playback.play()
        self.playback.on_end_of_track()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_tracklist
    def test_end_of_track_track_with_random_after_append_playlist(self):
        random.seed(1)
        self.tracklist.random = True
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[2])
        self.tracklist.add(self.tracks[:1])
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.next_track(tl_track),
                         self.tl_tracks[1])

    @populate_tracklist
    def test_previous_track_before_play(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.previous_track(tl_track), None)

    @populate_tracklist
    def test_previous_track_after_play(self):
        self.playback.play()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.previous_track(tl_track), None)

    @populate_tracklist
    def test_previous_track_after_next(self):
        self.playback.play()
        self.playback.next()
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.previous_track(tl_track),
                         self.tl_tracks[0])

    @populate_tracklist
    def test_previous_track_after_previous(self):
        self.playback.play()  # At track 0
        self.playback.next()  # At track 1
        self.playback.next()  # At track 2
        self.playback.previous()  # At track 1
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.previous_track(tl_track),
                         self.tl_tracks[0])

    def test_previous_track_empty_playlist(self):
        tl_track = self.playback.current_tl_track
        self.assertEqual(self.tracklist.previous_track(tl_track), None)

    @populate_tracklist
    def test_previous_track_with_consume(self):
        self.tracklist.consume = True
        for _ in self.tracks:
            self.playback.next()
            tl_track = self.playback.current_tl_track
            self.assertEqual(
                self.tracklist.previous_track(tl_track), tl_track)

    @populate_tracklist
    def test_previous_track_with_random(self):
        self.tracklist.random = True
        for _ in self.tracks:
            self.playback.next()
            tl_track = self.playback.current_tl_track
            self.assertEqual(
                self.tracklist.previous_track(tl_track), tl_track)

    def test_add_appends_to_the_tracklist(self):
        self.tracklist.add([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.tracklist.tracks), 2)
        self.tracklist.add([Track(uri='c'), Track(uri='d')])
        self.assertEqual(len(self.tracklist.tracks), 4)
        self.assertEqual(self.tracklist.tracks[0].uri, 'a')
        self.assertEqual(self.tracklist.tracks[1].uri, 'b')
        self.assertEqual(self.tracklist.tracks[2].uri, 'c')
        self.assertEqual(self.tracklist.tracks[3].uri, 'd')

    def test_add_does_not_reset_version(self):
        version = self.tracklist.version
        self.tracklist.add([])
        self.assertEqual(self.tracklist.version, version)

    @populate_tracklist
    def test_add_preserves_playing_state(self):
        self.playback.play()
        track = self.playback.current_track
        self.tracklist.add(self.tracklist.tracks[1:2])
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
        self.assertEqual(self.playback.current_track, track)

    @populate_tracklist
    def test_add_preserves_stopped_state(self):
        self.tracklist.add(self.tracklist.tracks[1:2])
        self.assertEqual(self.playback.state, PlaybackState.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_tracklist
    def test_add_returns_the_tl_tracks_that_was_added(self):
        tl_tracks = self.tracklist.add(self.tracklist.tracks[1:2])
        self.assertEqual(tl_tracks[0].track, self.tracklist.tracks[1])

    def test_index_returns_index_of_track(self):
        tl_tracks = self.tracklist.add(self.tracks)
        self.assertEquals(0, self.tracklist.index(tl_tracks[0]))
        self.assertEquals(1, self.tracklist.index(tl_tracks[1]))
        self.assertEquals(2, self.tracklist.index(tl_tracks[2]))

    def test_index_returns_none_if_item_not_found(self):
        index = self.tracklist.index(TlTrack(0, Track()))
        self.assertEquals(None, index)

    @populate_tracklist
    def test_move_single(self):
        self.tracklist.move(0, 0, 2)

        tracks = self.tracklist.tracks
        self.assertEqual(tracks[2], self.tracks[0])

    @populate_tracklist
    def test_move_group(self):
        self.tracklist.move(0, 2, 1)

        tracks = self.tracklist.tracks
        self.assertEqual(tracks[1], self.tracks[0])
        self.assertEqual(tracks[2], self.tracks[1])

    @populate_tracklist
    def test_moving_track_outside_of_playlist(self):
        tracks = len(self.tracklist.tracks)
        test = lambda: self.tracklist.move(0, 0, tracks + 5)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_move_group_outside_of_playlist(self):
        tracks = len(self.tracklist.tracks)
        test = lambda: self.tracklist.move(0, 2, tracks + 5)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_move_group_out_of_range(self):
        tracks = len(self.tracklist.tracks)
        test = lambda: self.tracklist.move(tracks + 2, tracks + 3, 0)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_move_group_invalid_group(self):
        test = lambda: self.tracklist.move(2, 1, 0)
        self.assertRaises(AssertionError, test)

    def test_tracks_attribute_is_immutable(self):
        tracks1 = self.tracklist.tracks
        tracks2 = self.tracklist.tracks
        self.assertNotEqual(id(tracks1), id(tracks2))

    @populate_tracklist
    def test_remove(self):
        track1 = self.tracklist.tracks[1]
        track2 = self.tracklist.tracks[2]
        version = self.tracklist.version
        self.tracklist.remove(uri=track1.uri)
        self.assertLess(version, self.tracklist.version)
        self.assertNotIn(track1, self.tracklist.tracks)
        self.assertEqual(track2, self.tracklist.tracks[1])

    @populate_tracklist
    def test_removing_track_that_does_not_exist_does_nothing(self):
        self.tracklist.remove(uri='/nonexistant')

    def test_removing_from_empty_playlist_does_nothing(self):
        self.tracklist.remove(uri='/nonexistant')

    @populate_tracklist
    def test_shuffle(self):
        random.seed(1)
        self.tracklist.shuffle()

        shuffled_tracks = self.tracklist.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_shuffle_subset(self):
        random.seed(1)
        self.tracklist.shuffle(1, 3)

        shuffled_tracks = self.tracklist.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_shuffle_invalid_subset(self):
        test = lambda: self.tracklist.shuffle(3, 1)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_shuffle_superset(self):
        tracks = len(self.tracklist.tracks)
        test = lambda: self.tracklist.shuffle(1, tracks + 5)
        self.assertRaises(AssertionError, test)

    @populate_tracklist
    def test_shuffle_open_subset(self):
        random.seed(1)
        self.tracklist.shuffle(1)

        shuffled_tracks = self.tracklist.tracks

        self.assertNotEqual(self.tracks, shuffled_tracks)
        self.assertEqual(self.tracks[0], shuffled_tracks[0])
        self.assertEqual(set(self.tracks), set(shuffled_tracks))

    @populate_tracklist
    def test_slice_returns_a_subset_of_tracks(self):
        track_slice = self.tracklist.slice(1, 3)
        self.assertEqual(2, len(track_slice))
        self.assertEqual(self.tracks[1], track_slice[0].track)
        self.assertEqual(self.tracks[2], track_slice[1].track)

    @populate_tracklist
    def test_slice_returns_empty_list_if_indexes_outside_tracks_list(self):
        self.assertEqual(0, len(self.tracklist.slice(7, 8)))
        self.assertEqual(0, len(self.tracklist.slice(-1, 1)))

    def test_version_does_not_change_when_adding_nothing(self):
        version = self.tracklist.version
        self.tracklist.add([])
        self.assertEquals(version, self.tracklist.version)

    def test_version_increases_when_adding_something(self):
        version = self.tracklist.version
        self.tracklist.add([Track()])
        self.assertLess(version, self.tracklist.version)
