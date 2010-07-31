import os
import random
import shutil
import tempfile
import threading
import time

from mopidy import settings
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Playlist, Track, Album, Artist

from tests import SkipTest, data_folder

__all__ = ['BaseCurrentPlaylistControllerTest',
           'BasePlaybackControllerTest',
           'BaseStoredPlaylistsControllerTest',
           'BaseLibraryControllerTest']

def populate_playlist(func):
    def wrapper(self):
        for track in self.tracks:
            self.backend.current_playlist.add(track)
        return func(self)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


class BaseCurrentPlaylistControllerTest(object):
    tracks = []
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class(mixer=DummyMixer())
        self.controller = self.backend.current_playlist
        self.playback = self.backend.playback

        assert len(self.tracks) == 3, 'Need three tracks to run tests.'

    def tearDown(self):
        self.backend.destroy()

    def test_add(self):
        for track in self.tracks:
            self.controller.add(track)
            self.assertEqual(track, self.controller.tracks[-1])

    def test_add_at_position(self):
        for track in self.tracks[:-1]:
            self.controller.add(track, 0)
            self.assertEqual(track, self.controller.tracks[0])

    @populate_playlist
    def test_add_at_position_outside_of_playlist(self):
        test = lambda: self.controller.add(self.tracks[0], len(self.tracks)+2)
        self.assertRaises(AssertionError, test)

    @populate_playlist
    def test_add_sets_id_property(self):
        for track in self.controller.tracks:
            self.assertNotEqual(None, track.id)

    @populate_playlist
    def test_get_by_cpid(self):
        cp_track = self.controller.cp_tracks[1]
        self.assertEqual(cp_track, self.controller.get(cpid=cp_track[0]))

    @populate_playlist
    def test_get_by_id(self):
        cp_track = self.controller.cp_tracks[1]
        self.assertEqual(cp_track, self.controller.get(id=cp_track[1].id))

    @populate_playlist
    def test_get_by_id_raises_error_for_invalid_id(self):
        self.assertRaises(LookupError, lambda: self.controller.get(id=1337))

    @populate_playlist
    def test_get_by_uri(self):
        cp_track = self.controller.cp_tracks[1]
        self.assertEqual(cp_track, self.controller.get(uri=cp_track[1].uri))

    @populate_playlist
    def test_get_by_uri_raises_error_for_invalid_id(self):
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

    def test_load(self):
        tracks = []
        self.assertNotEqual(id(tracks), id(self.controller.tracks))
        self.controller.load(tracks)
        self.assertEqual(tracks, self.controller.tracks)

    def test_get_by_id_returns_unique_match(self):
        track = Track(id=1)
        self.controller.load([Track(id=13), track, Track(id=17)])
        self.assertEqual(track, self.controller.get(id=1)[1])

    def test_get_by_id_raises_error_if_multiple_matches(self):
        track = Track(id=1)
        self.controller.load([Track(id=13), track, track])
        try:
            self.controller.get(id=1)
            self.fail(u'Should raise LookupError if multiple matches')
        except LookupError as e:
            self.assertEqual(u'"id=1" match multiple tracks', e[0])

    def test_get_by_id_raises_error_if_no_match(self):
        self.controller.playlist = Playlist(tracks=[Track(id=13), Track(id=17)])
        try:
            self.controller.get(id=1)
            self.fail(u'Should raise LookupError if no match')
        except LookupError as e:
            self.assertEqual(u'"id=1" match no tracks', e[0])

    def test_get_by_uri_returns_unique_match(self):
        track = Track(uri='a')
        self.controller.load([Track(uri='z'), track, Track(uri='y')])
        self.assertEqual(track, self.controller.get(uri='a')[1])

    def test_get_by_uri_raises_error_if_multiple_matches(self):
        track = Track(uri='a')
        self.controller.load([Track(uri='z'), track, track])
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
        track1 = Track(id=1, uri='a')
        track2 = Track(id=1, uri='b')
        track3 = Track(id=2, uri='b')
        self.controller.load([track1, track2, track3])
        self.assertEqual(track1, self.controller.get(id=1, uri='a')[1])
        self.assertEqual(track2, self.controller.get(id=1, uri='b')[1])
        self.assertEqual(track3, self.controller.get(id=2, uri='b')[1])

    def test_get_by_criteria_that_is_not_present_in_all_elements(self):
        track1 = Track(id=1)
        track2 = Track(uri='b')
        track3 = Track(id=2)
        self.controller.load([track1, track2, track3])
        self.assertEqual(track1, self.controller.get(id=1)[1])

    @populate_playlist
    def test_load_replaces_playlist(self):
        self.backend.current_playlist.load([])
        self.assertEqual(len(self.backend.current_playlist.tracks), 0)

    def test_load_does_not_reset_version(self):
        version = self.controller.version
        self.controller.load([])
        self.assertEqual(self.controller.version, version + 1)

    @populate_playlist
    def test_load_preserves_playing_state(self):
        tracks = self.controller.tracks
        playback = self.playback

        self.playback.play()
        self.controller.load([tracks[1]])
        self.assertEqual(playback.state, playback.PLAYING)
        self.assertEqual(tracks[1], self.playback.current_track)

    @populate_playlist
    def test_load_preserves_stopped_state(self):
        tracks = self.controller.tracks
        playback = self.playback

        self.controller.load([tracks[2]])
        self.assertEqual(playback.state, playback.STOPPED)
        self.assertEqual(None, self.playback.current_track)

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
        self.controller.remove(id=track1.id)
        self.assert_(version < self.controller.version)
        self.assert_(track1 not in self.controller.tracks)
        self.assertEqual(track2, self.controller.tracks[1])

    @populate_playlist
    def test_removing_track_that_does_not_exist(self):
        test = lambda: self.controller.remove(id=12345)
        self.assertRaises(LookupError, test)

    def test_removing_from_empty_playlist(self):
        test = lambda: self.controller.remove(id=12345)
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

    def test_version(self):
        version = self.controller.version
        self.controller.load([])
        self.assert_(version < self.controller.version)


class BasePlaybackControllerTest(object):
    tracks = []
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class(mixer=DummyMixer())
        self.playback = self.backend.playback
        self.current_playlist = self.backend.current_playlist

        assert len(self.tracks) >= 3, \
            'Need at least three tracks to run tests.'
        assert self.tracks[0].length >= 2000, \
            'First song needs to be at least 2000 miliseconds'

    def tearDown(self):
        self.backend.destroy()

    def test_initial_state_is_stopped(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_play_with_empty_playlist(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_play_with_empty_playlist_return_value(self):
        self.assertEqual(self.playback.play(), None)

    @populate_playlist
    def test_play_state(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_return_value(self):
        self.assertEqual(self.playback.play(), None)

    @populate_playlist
    def test_play_track_state(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_track_return_value(self):
        self.assertEqual(self.playback.play(
            self.current_playlist.cp_tracks[-1]), None)

    @populate_playlist
    def test_play_when_playing(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.play()
        self.assertEqual(track, self.playback.current_track)

    @populate_playlist
    def test_play_when_paused(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.pause()
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(track, self.playback.current_track)

    @populate_playlist
    def test_play_sets_current_track(self):
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_play_track_sets_current_track(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.assertEqual(self.playback.current_track, self.tracks[-1])

    @populate_playlist
    def test_current_track_after_completed_playlist(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.end_of_track_callback()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_next(self):
        self.playback.play()

        old_position = self.playback.current_playlist_position
        old_uri = self.playback.current_track.uri

        self.playback.next()

        self.assertEqual(self.playback.current_playlist_position,
            old_position+1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

    @populate_playlist
    def test_next_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.next(), None)

    @populate_playlist
    def test_next_does_not_trigger_playback(self):
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_next_at_end_of_playlist(self):
        self.playback.play()

        for i, track in enumerate(self.tracks):
            self.assertEqual(self.playback.state, self.playback.PLAYING)
            self.assertEqual(self.playback.current_track, track)
            self.assertEqual(self.playback.current_playlist_position, i)

            self.playback.next()

        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_next_until_end_of_playlist_and_play_from_start(self):
        self.playback.play()

        for track in self.tracks:
            self.playback.next()

        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, self.tracks[0])

    def test_next_for_empty_playlist(self):
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_previous(self):
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_previous_more(self):
        self.playback.play() # At track 0
        self.playback.next() # At track 1
        self.playback.next() # At track 2
        self.playback.previous() # At track 1
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_previous_return_value(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.previous(), None)

    @populate_playlist
    def test_previous_does_not_trigger_playback(self):
        self.playback.play()
        self.playback.next()
        self.playback.stop()
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_previous_at_start_of_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    def test_previous_for_empty_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_next_track_before_play(self):
        self.assertEqual(self.playback.next_track, self.tracks[0])

    @populate_playlist
    def test_next_track_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.next_track, self.tracks[1])

    @populate_playlist
    def test_next_track_after_previous(self):
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.next_track, self.tracks[1])

    def test_next_track_empty_playlist(self):
        self.assertEqual(self.playback.next_track, None)

    @populate_playlist
    def test_next_track_at_end_of_playlist(self):
        self.playback.play()
        for track in self.current_playlist.cp_tracks[1:]:
            self.playback.next()
        self.assertEqual(self.playback.next_track, None)

    @populate_playlist
    def test_next_track_at_end_of_playlist_with_repeat(self):
        self.playback.repeat = True
        self.playback.play()
        for track in self.tracks[1:]:
            self.playback.next()
        self.assertEqual(self.playback.next_track, self.tracks[0])

    @populate_playlist
    def test_next_track_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.assertEqual(self.playback.next_track, self.tracks[2])

    @populate_playlist
    def test_previous_track_before_play(self):
        self.assertEqual(self.playback.previous_track, None)

    @populate_playlist
    def test_previous_track_after_play(self):
        self.playback.play()
        self.assertEqual(self.playback.previous_track, None)

    @populate_playlist
    def test_previous_track_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.previous_track, self.tracks[0])

    @populate_playlist
    def test_previous_track_after_previous(self):
        self.playback.play() # At track 0
        self.playback.next() # At track 1
        self.playback.next() # At track 2
        self.playback.previous() # At track 1
        self.assertEqual(self.playback.previous_track, self.tracks[0])

    def test_previous_track_empty_playlist(self):
        self.assertEqual(self.playback.previous_track, None)

    @populate_playlist
    def test_previous_track_with_consume(self):
        self.playback.consume = True
        for track in self.tracks:
            self.playback.next()
            self.assertEqual(self.playback.previous_track,
                self.playback.current_track)

    @populate_playlist
    def test_previous_track_with_random(self):
        self.playback.random = True
        for track in self.tracks:
            self.playback.next()
            self.assertEqual(self.playback.previous_track,
                self.playback.current_track)

    @populate_playlist
    def test_initial_current_track(self):
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_current_track_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_current_track_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_initial_current_playlist_position(self):
        self.assertEqual(self.playback.current_playlist_position, None)

    @populate_playlist
    def test_current_playlist_position_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.current_playlist_position, 0)

    @populate_playlist
    def test_current_playlist_position_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_playlist_position, 1)

    @populate_playlist
    def test_current_playlist_position_at_end_of_playlist(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.end_of_track_callback()
        self.assertEqual(self.playback.current_playlist_position, None)

    def test_new_playlist_loaded_callback_gets_called(self):
        callback = self.playback.new_playlist_loaded_callback

        def wrapper():
            wrapper.called = True
            return callback()
        wrapper.called = False

        self.playback.new_playlist_loaded_callback = wrapper
        self.backend.current_playlist.load([])

        self.assert_(wrapper.called)

    @populate_playlist
    def test_end_of_track_callback_gets_called(self):
        end_of_track_callback = self.playback.end_of_track_callback
        event = threading.Event()

        def wrapper():
            result = end_of_track_callback()
            event.set()
            return result

        self.playback.end_of_track_callback = wrapper

        self.playback.play()
        self.playback.seek(self.tracks[0].length - 10)

        event.wait(5)

        self.assert_(event.is_set())

    @populate_playlist
    def test_new_playlist_loaded_callback_when_playing(self):
        self.playback.play()
        self.backend.current_playlist.load([self.tracks[2]])
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_playlist
    def test_new_playlist_loaded_callback_when_stopped(self):
        self.backend.current_playlist.load([self.tracks[2]])
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.next_track, self.tracks[2])

    @populate_playlist
    def test_new_playlist_loaded_callback_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.backend.current_playlist.load([self.tracks[2]])
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)
        self.assertEqual(self.playback.next_track, self.tracks[2])

    @populate_playlist
    def test_pause_when_stopped(self):
        self.playback.pause()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_pause_when_playing(self):
        self.playback.play()
        self.playback.pause()
        self.assertEqual(self.playback.state, self.playback.PAUSED)

    @populate_playlist
    def test_pause_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.pause()
        self.assertEqual(self.playback.state, self.playback.PAUSED)

    @populate_playlist
    def test_pause_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.pause(), None)

    @populate_playlist
    def test_resume_when_stopped(self):
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_resume_when_playing(self):
        self.playback.play()
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_resume_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_resume_return_value(self):
        self.playback.play()
        self.playback.pause()
        self.assertEqual(self.playback.resume(), None)

    @populate_playlist
    def test_resume_continues_from_right_position(self):
        self.playback.play()
        time.sleep(0.2)
        self.playback.pause()
        self.playback.resume()
        self.assertNotEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_seek_when_stopped(self):
        self.playback.seek(1000)
        position = self.playback.time_position
        self.assert_(position >= 990, position)

    def test_seek_on_empty_playlist(self):
        self.playback.seek(0)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_seek_when_stopped_triggers_play(self):
        self.playback.seek(0)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_seek_when_playing(self):
        length = self.backend.current_playlist.tracks[0].length
        self.playback.play()
        self.playback.seek(length - 1000)
        position = self.playback.time_position
        self.assert_(position >= length - 1010, position)

    @populate_playlist
    def test_seek_when_paused(self):
        length = self.backend.current_playlist.tracks[0].length
        self.playback.play()
        self.playback.pause()
        self.playback.seek(length - 1000)
        position = self.playback.time_position
        self.assert_(position >= length - 1010, position)

    @populate_playlist
    def test_seek_when_paused_triggers_play(self):
        self.playback.play()
        self.playback.pause()
        self.playback.seek(0)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_seek_beyond_end_of_song(self):
        self.playback.play()
        self.playback.seek(self.tracks[0].length*100)
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_seek_beyond_end_of_song_for_last_track(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.seek(self.current_playlist.tracks[-1].length * 100)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_seek_beyond_start_of_song(self):
        self.playback.play()
        self.playback.seek(-1000)
        position = self.playback.time_position
        self.assert_(position >= 0, position)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_seek_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.seek(0), None)

    @populate_playlist
    def test_stop_when_stopped(self):
        self.playback.stop()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_stop_when_playing(self):
        self.playback.play()
        self.playback.stop()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_stop_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.stop()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_stop_return_value(self):
        self.playback.play()
        self.assertEqual(self.playback.stop(), None)

    def test_time_position_when_stopped(self):
        self.assertEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_time_position_when_stopped_with_playlist(self):
        self.assertEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_time_position_when_playing(self):
        self.playback.play()
        first = self.playback.time_position
        time.sleep(1)
        second = self.playback.time_position

        self.assert_(second > first, '%s - %s' % (first, second))

    @populate_playlist
    def test_time_position_when_paused(self):
        self.playback.play()
        time.sleep(0.2)
        self.playback.pause()
        time.sleep(0.2)
        first = self.playback.time_position
        second = self.playback.time_position

        self.assertEqual(first, second)

    @populate_playlist
    def test_play_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[0])

    @populate_playlist
    def test_next_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        self.playback.next()
        self.assert_(self.tracks[0] not in self.backend.current_playlist.tracks)

    @populate_playlist
    def test_playlist_is_empty_after_all_tracks_are_played_with_consume(self):
        self.playback.consume = True
        self.playback.play()
        for i in range(len(self.backend.current_playlist.tracks)):
            self.playback.next()
        self.assertEqual(len(self.backend.current_playlist.tracks), 0)

    @populate_playlist
    def test_play_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.assertEqual(self.playback.current_track, self.tracks[2])

    @populate_playlist
    def test_next_with_random(self):
        # FIXME feels very fragile
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_previous_with_random(self):
        random.seed(1)
        self.playback.random = True
        self.playback.play()
        self.playback.next()
        current_track = self.playback.current_track
        self.playback.previous()
        self.assertEqual(self.playback.current_track, current_track)

    @populate_playlist
    def test_end_of_song_starts_next_track(self):
        self.playback.play()
        self.playback.end_of_track_callback()
        self.assertEqual(self.playback.current_track, self.tracks[1])

    @populate_playlist
    def test_end_of_playlist_stops(self):
        self.playback.play(self.current_playlist.cp_tracks[-1])
        self.playback.end_of_track_callback()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_repeat_off_by_default(self):
        self.assertEqual(self.playback.repeat, False)

    def test_random_off_by_default(self):
        self.assertEqual(self.playback.random, False)

    def test_consume_off_by_default(self):
        self.assertEqual(self.playback.consume, False)

    @populate_playlist
    def test_random_until_end_of_playlist(self):
        self.playback.random = True
        self.playback.play()
        for track in self.tracks[1:]:
            self.playback.next()
        self.assertEqual(self.playback.next_track, None)

    @populate_playlist
    def test_random_until_end_of_playlist_and_play_from_start(self):
        self.playback.repeat = True
        for track in self.tracks:
            self.playback.next()
        self.assertNotEqual(self.playback.next_track, None)
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_random_until_end_of_playlist_with_repeat(self):
        self.playback.repeat = True
        self.playback.random = True
        self.playback.play()
        for track in self.tracks:
            self.playback.next()
        self.assertNotEqual(self.playback.next_track, None)

    @populate_playlist
    def test_next_track_with_random_after_load_playlist(self):
        random.seed(1)
        self.playback.random = True
        self.assertEqual(self.playback.next_track, self.tracks[2])
        self.backend.current_playlist.load(self.tracks[:1])
        self.assertEqual(self.playback.next_track, self.tracks[0])

    @populate_playlist
    def test_played_track_during_random_not_played_again(self):
        self.playback.random = True
        self.playback.play()
        played = []
        for track in self.tracks:
            self.assert_(self.playback.current_track not in played)
            played.append(self.playback.current_track)
            self.playback.next()

    def test_playing_track_with_invalid_uri(self):
        self.backend.current_playlist.load([Track(uri='foobar')])
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_playing_track_that_isnt_in_playlist(self):
        test = lambda: self.playback.play(self.tracks[0])
        self.assertRaises(AssertionError, test)


class BaseStoredPlaylistsControllerTest(object):
    backend_class = None

    def setUp(self):
        self.original_playlist_folder = settings.LOCAL_PLAYLIST_FOLDER
        self.original_tag_cache = settings.LOCAL_TAG_CACHE
        self.original_music_folder = settings.LOCAL_MUSIC_FOLDER

        settings.LOCAL_PLAYLIST_FOLDER = tempfile.mkdtemp()
        settings.LOCAL_TAG_CACHE = data_folder('library_tag_cache')
        settings.LOCAL_MUSIC_FOLDER = data_folder('')

        self.backend = self.backend_class(mixer=DummyMixer())
        self.stored  = self.backend.stored_playlists

    def tearDown(self):
        self.backend.destroy()

        if os.path.exists(settings.LOCAL_PLAYLIST_FOLDER):
            shutil.rmtree(settings.LOCAL_PLAYLIST_FOLDER)

        settings.LOCAL_PLAYLIST_FOLDER = self.original_playlist_folder
        settings.LOCAL_TAG_CACHE = self.original_tag_cache
        settings.LOCAL_MUSIC_FOLDER = self.original_music_folder

    def test_create(self):
        playlist = self.stored.create('test')
        self.assertEqual(playlist.name, 'test')

    def test_create_in_playlists(self):
        playlist = self.stored.create('test')
        self.assert_(self.stored.playlists)
        self.assert_(playlist in self.stored.playlists)

    def test_playlists_empty_to_start_with(self):
        self.assert_(not self.stored.playlists)

    def test_delete_non_existant_playlist(self):
        self.stored.delete(Playlist())

    def test_delete_playlist(self):
        playlist = self.stored.create('test')
        self.stored.delete(playlist)
        self.assert_(not self.stored.playlists)

    def test_get_without_criteria(self):
        test = self.stored.get
        self.assertRaises(LookupError, test)

    def test_get_with_wrong_cirteria(self):
        test = lambda: self.stored.get(name='foo')
        self.assertRaises(LookupError, test)

    def test_get_with_right_criteria(self):
        playlist1 = self.stored.create('test')
        playlist2 = self.stored.get(name='test')
        self.assertEqual(playlist1, playlist2)

    def test_get_by_name_returns_unique_match(self):
        playlist = Playlist(name='b')
        self.stored.playlists = [Playlist(name='a'), playlist]
        self.assertEqual(playlist, self.stored.get(name='b'))

    def test_get_by_name_returns_first_of_multiple_matches(self):
        playlist = Playlist(name='b')
        self.stored.playlists = [
            playlist, Playlist(name='a'), Playlist(name='b')]
        try:
            self.stored.get(name='b')
            self.fail(u'Should raise LookupError if multiple matches')
        except LookupError as e:
            self.assertEqual(u'"name=b" match multiple playlists', e[0])

    def test_get_by_id_raises_keyerror_if_no_match(self):
        self.stored.playlists = [Playlist(name='a'), Playlist(name='b')]
        try:
            self.stored.get(name='c')
            self.fail(u'Should raise LookupError if no match')
        except LookupError as e:
            self.assertEqual(u'"name=c" match no playlists', e[0])

    def test_search_returns_empty_list(self):
        self.assertEqual([], self.stored.search('test'))

    def test_search_returns_playlist(self):
        playlist = self.stored.create('test')
        playlists = self.stored.search('test')
        self.assert_(playlist in playlists)

    def test_search_returns_mulitple_playlists(self):
        playlist1 = self.stored.create('test')
        playlist2 = self.stored.create('test2')
        playlists = self.stored.search('test')
        self.assert_(playlist1 in playlists)
        self.assert_(playlist2 in playlists)

    def test_lookup(self):
        raise SkipTest

    def test_refresh(self):
        raise SkipTest

    def test_rename(self):
        playlist = self.stored.create('test')
        self.stored.rename(playlist, 'test2')
        self.stored.get(name='test2')

    def test_rename_unknown_playlist(self):
        self.stored.rename(Playlist(), 'test2')
        test = lambda: self.stored.get(name='test2')
        self.assertRaises(LookupError, test)

    def test_save(self):
        # FIXME should we handle playlists without names?
        playlist = Playlist(name='test')
        self.stored.save(playlist)
        self.assert_(playlist in self.stored.playlists)

    def test_playlist_with_unknown_track(self):
        raise SkipTest


class BaseLibraryControllerTest(object):
    artists = [Artist(name='artist1'), Artist(name='artist2'), Artist()]
    albums = [Album(name='album1', artists=artists[:1]),
        Album(name='album2', artists=artists[1:2]),
        Album()]
    tracks = [Track(name='track1', length=4000, artists=artists[:1],
            album=albums[0], uri='file://' + data_folder('uri1'), id=0),
        Track(name='track2', length=4000, artists=artists[1:2],
            album=albums[1], uri='file://' + data_folder('uri2'), id=1),
        Track(id=3)]

    def setUp(self):
        self.backend = self.backend_class(mixer=DummyMixer())
        self.library = self.backend.library

    def tearDown(self):
        self.backend.destroy()

    def test_refresh(self):
        self.library.refresh()

    def test_refresh_uri(self):
        raise SkipTest

    def test_refresh_missing_uri(self):
        raise SkipTest

    def test_lookup(self):
        track = self.library.lookup(self.tracks[0].uri)
        self.assertEqual(track, self.tracks[0])

    def test_lookup_unknown_track(self):
        test = lambda: self.library.lookup('fake uri')
        self.assertRaises(LookupError, test)

    def test_find_exact_no_hits(self):
        result = self.library.find_exact('track', 'unknown track')
        self.assertEqual(result, Playlist())

        result = self.library.find_exact('artist', 'unknown artist')
        self.assertEqual(result, Playlist())

        result = self.library.find_exact('album', 'unknown artist')
        self.assertEqual(result, Playlist())

    def test_find_exact_artist(self):
        result = self.library.find_exact('artist', 'artist1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.find_exact('artist', 'artist2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_find_exact_track(self):
        result = self.library.find_exact('track', 'track1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.find_exact('track', 'track2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_find_exact_album(self):
        result = self.library.find_exact('album', 'album1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.find_exact('album', 'album2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_find_exact_wrong_type(self):
        test = lambda: self.library.find_exact('wrong', 'test')
        self.assertRaises(LookupError, test)

    def test_find_exact_with_empty_query(self):
        test = lambda: self.library.find_exact('artist', '')
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact('track', '')
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact('album', '')
        self.assertRaises(LookupError, test)

    def test_search_no_hits(self):
        result = self.library.search('track', 'unknown track')
        self.assertEqual(result, Playlist())

        result = self.library.search('artist', 'unknown artist')
        self.assertEqual(result, Playlist())

        result = self.library.search('album', 'unknown artist')
        self.assertEqual(result, Playlist())

        result = self.library.search('uri', 'unknown')
        self.assertEqual(result, Playlist())

        result = self.library.search('any', 'unknown')
        self.assertEqual(result, Playlist())

    def test_search_artist(self):
        result = self.library.search('artist', 'Tist1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search('artist', 'Tist2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_track(self):
        result = self.library.search('track', 'Rack1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search('track', 'Rack2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_album(self):
        result = self.library.search('album', 'Bum1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search('album', 'Bum2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_uri(self):
        result = self.library.search('uri', 'RI1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search('uri', 'RI2')
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_any(self):
        result = self.library.search('any', 'Tist1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))
        result = self.library.search('any', 'Rack1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))
        result = self.library.search('any', 'Bum1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))
        result = self.library.search('any', 'RI1')
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

    def test_search_wrong_type(self):
        test = lambda: self.library.search('wrong', 'test')
        self.assertRaises(LookupError, test)

    def test_search_with_empty_query(self):
        test = lambda: self.library.search('artist', '')
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search('track', '')
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search('album', '')
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search('uri', '')
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search('any', '')
        self.assertRaises(LookupError, test)
