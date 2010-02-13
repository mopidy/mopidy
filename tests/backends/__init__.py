import random

from mopidy.models import Track, Playlist

def populate_playlist(func):
    def wrapper(self):
        for uri in self.uris:
            self.backend.current_playlist.add(uri)

        return func(self)

    return wrapper

class BaseCurrentPlaylistControllerTest(object):
    uris = []
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class()
        self.controller = self.backend.current_playlist
        self.playback = self.backend.playback

        assert len(self.uris) >= 3, 'Need at least three urls to run tests.'

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
    def test_get_by_id(self):
        track = self.controller.playlist.tracks[1]
        self.assertEqual(track, self.controller.get_by_id(track.id))

    @populate_playlist
    def test_get_by_id_raises_error_for_invalid_id(self):
        self.assertRaises(self.controller.get_by_id(1337))

    @populate_playlist
    def test_get_by_url(self):
        track = self.controller.playlist.tracks[1]
        self.assertEqual(track, self.controller.get_by_url(track.uri))

    @populate_playlist
    def test_get_by_url_raises_error_for_invalid_id(self):
        self.assertRaises(self.controller.get_by_url('foobar'))

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
    def test_load_preserves_and_updates_play_state(self):
        tracks = self.controller.playlist.tracks
        playback = self.playback

        self.playback.play()
        self.controller.load(Playlist(tracks=[tracks[1]]))
        self.assertEqual(playback.state, playback.PLAYING)
        self.assertEqual(tracks[1], self.playback.current_track)

        self.playback.stop()
        self.controller.load(Playlist(tracks=[tracks[2]]))
        self.assertEqual(playback.state, playback.STOPPED)
        self.assertEqual(tracks[2], self.playback.current_track)

    def test_load_triggers_playing_of_new_playlist_if_allready_playing(self):
        raise NotImplementedError

    @populate_playlist
    def test_move_single(self):
        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[0].uri, self.uris[0])

        self.controller.move(0, 0, 2)

        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[2].uri, self.uris[0])

    @populate_playlist
    def test_move_group(self):
        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[0].uri, self.uris[0])
        self.assertEqual(tracks[1].uri, self.uris[1])

        self.controller.move(0, 2, 1)

        tracks = self.controller.playlist.tracks
        self.assertEqual(tracks[1].uri, self.uris[0])
        self.assertEqual(tracks[2].uri, self.uris[1])

    @populate_playlist
    def test_moving_track_outside_of_playlist(self):
        raise NotImplementedError

    def test_playlist_attribute_is_imutable(self):
        raise NotImplementedError

    @populate_playlist
    def test_remove(self):
        track1 = self.controller.playlist.tracks[1]
        track2 = self.controller.playlist.tracks[2]
        self.controller.remove(1)
        self.assert_(track1 not in self.controller.playlist.tracks)
        self.assertEqual(track2, self.controller.playlist.tracks[1])

    @populate_playlist
    def test_removing_track_that_does_not_exist(self):
        raise NotImplementedError

    def test_removing_from_empty_playlist(self):
        raise NotImplementedError

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

    def setUp(self):
        self.backend = self.backend_class()
        self.playback = self.backend.playback

    def test_initial_state_is_stopped(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    def test_play_with_empty_playlist(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

        result = self.playback.play()

        self.assertEqual(result, False)
        self.assertEqual(self.playback.state, self.playback.STOPPED)

    @populate_playlist
    def test_play(self):
        self.assertEqual(self.playback.state, self.playback.STOPPED)

        result = self.playback.play()

        self.assertEqual(result, True)
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    @populate_playlist
    def test_next(self):
        self.playback.play()

        old_position = self.playback.playlist_position
        old_uri = self.playback.current_track.uri

        self.playback.next()

        self.assertEqual(self.playback.playlist_position, old_position+1)
        self.assertNotEqual(self.playback.current_track.uri, old_uri)

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
