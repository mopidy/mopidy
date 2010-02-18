import random
import time

from mopidy.models import Playlist, Track

def populate_playlist(func):
    def wrapper(self):
        for uri in self.uris:
            self.backend.current_playlist.add(uri)
        return func(self)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

class BaseCurrentPlaylistControllerTest(object):
    uris = []
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class()
        self.controller = self.backend.current_playlist
        self.playback = self.backend.playback

        assert len(self.uris) >= 3, 'Need at least three urls to run tests.'

    def tearDown(self):
        self.backend.destroy()

    def test_add(self):
        for uri in self.uris:
            self.controller.add(uri)
            self.assertEqual(uri, self.controller.playlist.tracks[-1].uri)

    def test_add_at_position(self):
        for uri in self.uris[:-1]:
            self.controller.add(uri, 0)
            self.assertEqual(uri, self.controller.playlist.tracks[0].uri)

    @populate_playlist
    def test_add_at_position_outside_of_playlist(self):
        uri = self.uris[0]

        self.controller.add(uri, len(self.uris)+2)
        self.assertEqual(uri, self.controller.playlist.tracks[-1].uri)

    @populate_playlist
    def test_add_sets_id_property(self):
        for track in self.controller.playlist.tracks:
            self.assertNotEqual(None, track.id)

    @populate_playlist
    def test_get_by_id(self):
        track = self.controller.playlist.tracks[1]
        self.assertEqual(track, self.controller.get_by_id(track.id))

    @populate_playlist
    def test_get_by_id_raises_error_for_invalid_id(self):
        self.assertRaises(KeyError, lambda: self.controller.get_by_id(1337))

    @populate_playlist
    def test_get_by_url(self):
        track = self.controller.playlist.tracks[1]
        self.assertEqual(track, self.controller.get_by_url(track.uri))

    @populate_playlist
    def test_get_by_url_raises_error_for_invalid_id(self):
        self.assertRaises(KeyError, lambda: self.controller.get_by_url('foobar'))

    @populate_playlist
    def test_clear(self):
        self.controller.clear()
        self.assertEqual(len(self.controller.playlist.tracks), 0)

    def test_clear_empty_playlist(self):
        self.controller.clear()

    @populate_playlist
    def test_clear_when_playing(self):
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.controller.clear()
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_load(self):
        new_playlist = Playlist()
        self.assertNotEqual(new_playlist, self.controller.playlist)
        self.controller.load(new_playlist)
        self.assertEqual(new_playlist, self.controller.playlist)

    def test_load_does_not_reset_version(self):
        version = self.controller.version

        self.controller.load(Playlist())
        self.assertEqual(self.controller.version, version+1)

    @populate_playlist
    def test_load_preserves_playing_state(self):
        tracks = self.controller.playlist.tracks
        playback = self.playback

        self.playback.play()
        self.controller.load(Playlist(tracks=[tracks[1]]))
        self.assertEqual(playback.state, playback.PLAYING)
        self.assertEqual(tracks[1], self.playback.current_track)

    @populate_playlist
    def test_load_preserves_stopped_state(self):
        tracks = self.controller.playlist.tracks
        playback = self.playback

        self.controller.load(Playlist(tracks=[tracks[2]]))
        self.assertEqual(playback.state, playback.STOPPED)
        self.assertEqual(None, self.playback.current_track)

    @populate_playlist
    def test_move_single(self):
        self.controller.move(0, 0, 2)

        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[2].uri, self.uris[0])

    @populate_playlist
    def test_move_group(self):
        self.controller.move(0, 2, 1)

        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[1].uri, self.uris[0])
        self.assertEqual(tracks[2].uri, self.uris[1])

    @populate_playlist
    def test_moving_track_outside_of_playlist(self):
        tracks = self.controller.playlist.tracks

        self.controller.move(0, 0, len(tracks)+5)
        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[-1].uri, self.uris[0])

    @populate_playlist
    def test_move_group_outside_of_playlist(self):
        tracks = self.controller.playlist.tracks

        self.controller.move(0, 2, len(tracks)+5)

        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[-2].uri, self.uris[0])
        self.assertEqual(tracks[-1].uri, self.uris[1])

    def test_playlist_attribute_is_imutable(self):
        raise NotImplementedError # design decision needed

    @populate_playlist
    def test_remove(self):
        track1 = self.controller.playlist.tracks[1]
        track2 = self.controller.playlist.tracks[2]
        self.controller.remove(track1)
        self.assert_(track1 not in self.controller.playlist.tracks)
        self.assertEqual(track2, self.controller.playlist.tracks[1])

    @populate_playlist
    def test_removing_track_that_does_not_exist(self):
        self.controller.remove(Track())

    def test_removing_from_empty_playlist(self):
        self.controller.remove(Track())

    @populate_playlist
    def test_shuffle(self):
        tracks = self.controller.playlist.tracks
        random.seed(1)
        self.controller.shuffle()

        shuffled_tracks = self.controller.playlist.tracks

        self.assertNotEqual(tracks, shuffled_tracks)
        self.assertEqual(set(tracks), set(shuffled_tracks))

    @populate_playlist
    def test_shuffle_subset(self):
        tracks = self.controller.playlist.tracks
        random.seed(1)
        self.controller.shuffle(1, 3)

        shuffled_tracks = self.controller.playlist.tracks

        self.assertNotEqual(tracks, shuffled_tracks)
        self.assertEqual(tracks[0], shuffled_tracks[0])
        self.assertEqual(set(tracks), set(shuffled_tracks))

    def test_version(self):
        version = self.controller.version
        self.controller.playlist = Playlist()
        self.assertEqual(version+1, self.controller.version)

class BasePlaybackControllerTest(object):
    uris = []
    backend_class = None
    supports_volume = False

    def setUp(self):
        self.backend = self.backend_class()
        self.playback = self.backend.playback

        assert len(self.uris) >= 3, 'Need at least three urls to run tests.'

    def tearDown(self):
        self.backend.destroy()

    def test_initial_state_is_stopped(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_play_with_empty_playlist(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

        result = self.playback.play()

        self.assertEqual(result, False)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_play_state(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_return_value(self):
        self.assert_(self.playback.play())

    @populate_playlist
    def test_play_track_state(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.playback.play(tracks[-1])
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_track_return_value(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.assert_(self.playback.play(tracks[-1]))

    @populate_playlist
    def test_play_when_playing(self):
        self.playback.play()
        track = self.playback.current_track
        self.playback.play()
        self.assertEqual(track, self.playback.current_track)

    @populate_playlist
    def test_play_when_paused(self):
        self.playback.play()
        self.playback.pause()
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_play_sets_current_track(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.assertEqual(self.playback.current_track, tracks[0])

    @populate_playlist
    def test_play_track_sets_current_track(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play(tracks[-1])
        self.assertEqual(self.playback.current_track, tracks[-1])

    @populate_playlist
    def test_next(self):
        self.playback.play()

        old_position = self.playback.playlist_position
        old_uri = self.playback.current_track.uri

        self.playback.next()

        self.assertEqual(self.playback.playlist_position, old_position+1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

    def test_next_return_value(self):
        raise NotImplementedError # design decision needed

    @populate_playlist
    def test_next_triggers_playback(self):
        self.playback.next()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_next_at_end_of_playlist(self):
        playback = self.backend.playback
        tracks = self.backend.current_playlist.playlist.tracks

        playback.play()

        for i, track in enumerate(tracks):
            self.assertEqual(playback.state, playback.PLAYING)
            self.assertEqual(playback.current_track, track)
            self.assertEqual(playback.playlist_position, i)

            playback.next()

        self.assertEqual(playback.state, playback.STOPPED)
        self.assertEqual(playback.current_track, tracks[-1])
        self.assertEqual(playback.playlist_position, len(tracks) - 1)

    def test_next_for_empty_playlist(self):
        self.playback.next()

    @populate_playlist
    def test_previous(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.current_track, tracks[0])

    @populate_playlist
    def test_previous_more(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play() # At track 0
        self.playback.next() # At track 1
        self.playback.next() # At track 2
        self.playback.previous() # At track 1
        self.assertEqual(self.playback.current_track, tracks[1])

    def test_previous_return_value(self):
        raise NotImplementedError # design decision needed

    @populate_playlist
    def test_previous_triggers_playback(self):
        self.playback.play()
        self.playback.next()
        self.playback.stop()
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_previous_at_start_of_playlist(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.PLAYING)
        self.assertEqual(self.playback.current_track, tracks[0])

    def test_previous_for_empty_playlist(self):
        self.playback.previous()
        self.assertEqual(self.playback.state, self.playback.STOPPED)
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_next_track_before_play(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.assertEqual(self.playback.next_track, tracks[0])

    @populate_playlist
    def test_next_track_during_play(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.assertEqual(self.playback.next_track, tracks[1])

    @populate_playlist
    def test_next_track_after_previous(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.playback.next()
        self.playback.previous()
        self.assertEqual(self.playback.next_track, tracks[1])

    def test_next_track_empty_playlist(self):
        self.assertEqual(self.playback.next_track, None)

    @populate_playlist
    def test_next_track_at_end_of_playlist(self):
        for uri in self.uris:
            self.playback.next()
        self.assertEqual(self.playback.next_track, None)

    @populate_playlist
    def test_previous_track_before_play(self):
        self.assertEqual(self.playback.previous_track, None)

    @populate_playlist
    def test_previous_track_after_play(self):
        self.playback.play()
        self.assertEqual(self.playback.previous_track, None)

    @populate_playlist
    def test_previous_track_after_next(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.previous_track, tracks[0])

    @populate_playlist
    def test_previous_track_after_previous(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play() # At track 0
        self.playback.next() # At track 1
        self.playback.next() # At track 2
        self.playback.previous() # At track 1
        self.assertEqual(self.playback.previous_track, tracks[0])

    def test_previous_track_empty_playlist(self):
        self.assertEqual(self.playback.previous_track, None)

    @populate_playlist
    def test_initial_current_track(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.assertEqual(self.playback.current_track, None)

    @populate_playlist
    def test_current_track_during_play(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.assertEqual(self.playback.current_track, tracks[0])

    @populate_playlist
    def test_current_track_after_next(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.current_track, tracks[1])

    @populate_playlist
    def test_initial_playlist_position(self):
        self.assertEqual(self.playback.playlist_position, None)

    @populate_playlist
    def test_playlist_position_during_play(self):
        self.playback.play()
        self.assertEqual(self.playback.playlist_position, 0)

    @populate_playlist
    def test_playlist_position_after_next(self):
        self.playback.play()
        self.playback.next()
        self.assertEqual(self.playback.playlist_position, 1)

    def test_new_playlist_loaded_callback_gets_called(self):
        new_playlist_loaded_callback = self.playback.new_playlist_loaded_callback

        def wrapper():
            wrapper.called = True
            return new_playlist_loaded_callback()
        wrapper.called = False

        self.playback.new_playlist_loaded_callback = wrapper
        self.backend.current_playlist.load(Playlist())

        self.assert_(wrapper.called)

    @populate_playlist
    def test_new_playlist_loaded_callback_when_playing(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.backend.current_playlist.load(Playlist(tracks=[tracks[2]]))
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_new_playlist_loaded_callback_when_stopped(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.backend.current_playlist.load(Playlist(tracks=[tracks[2]]))
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_new_playlist_loaded_callback_when_paused(self):
        tracks = self.backend.current_playlist.playlist.tracks
        self.playback.play()
        self.playback.pause()
        self.backend.current_playlist.load(Playlist(tracks=[tracks[2]]))
        self.assertEqual(self.playback.state, self.playback.STOPPED)

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

    def test_pause_return_value(self):
        raise NotImplementedError # design decision needed

    @populate_playlist
    def test_resume_when_stopped(self):
        self.playback.resume()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

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

    def test_resume_return_value(self):
        raise NotImplementedError # design decision needed

    def test_resume_continues_from_right_position(self):
        raise NotImplementedError

    def test_seek_when_stopped(self):
        raise NotImplementedError

    def test_seek_when_playing(self):
        raise NotImplementedError

    def test_seek_when_paused(self):
        raise NotImplementedError

    def test_seek_return_value(self):
        raise NotImplementedError # design decision needed

    def test_seek_beyond_end_of_song(self):
        raise NotImplementedError

    def test_seek_beyond_start_of_song(self):
        raise NotImplementedError

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
        raise NotImplementedError # design decision needed

    def test_time_position_when_stopped(self):
        self.assertEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_time_position_when_stopped_with_playlist(self):
        self.assertEqual(self.playback.time_position, 0)

    @populate_playlist
    def test_time_position_when_playing(self):
        self.playback.play()
        time.sleep(0.1)
        first = self.playback.time_position
        time.sleep(0.1)
        second = self.playback.time_position

        self.assert_(second > first, '%s - %s' % (first, second))

    @populate_playlist
    def test_time_position_when_paused(self):
        self.playback.play()
        time.sleep(0.1)
        self.playback.pause()
        first = self.playback.time_position
        second = self.playback.time_position

        self.assertEqual(first, second)

    def test_volume(self):
        if not self.supports_volume:
            self.assertEqual(self.playback.volume, None)
        else:
            self.assertEqual(self.playback.volume, 100)
            self.playback.volume = 50
            self.assertEqual(self.playback.volume, 50)
            self.playback.volume = 0
            self.assertEqual(self.playback.volume, 0)

    def test_volume_is_not_float(self):
        if not self.supports_volume:
            return

        self.playback.volume = 1.0 / 3 * 100
        self.assertEqual(self.playback.volume, 33)

    def test_play_with_consume(self):
        raise NotImplementedError

    def test_next_with_consume(self):
        raise NotImplementedError

    def test_previous_track_with_consume(self):
        raise NotImplementedError

    def test_play_with_shuffle(self):
        raise NotImplementedError

    def test_next_with_shuffle(self):
        raise NotImplementedError

    def test_previous_with_shuffle(self):
        raise NotImplementedError

    def test_next_track_with_shuffle(self):
        raise NotImplementedError

    def test_previous_track_with_shuffle(self):
        raise NotImplementedError

    def test_end_of_song_starts_next_track(self):
        raise NotImplementedError

    def test_end_of_playlist_stops(self):
        raise NotImplementedError
