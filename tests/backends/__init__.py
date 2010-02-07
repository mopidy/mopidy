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

    def test_uri_set(self):
        self.assert_(len(self.uris) >= 3)

    def test_add(self):
        controller = self.backend.current_playlist

        for uri in self.uris:
            controller.add(uri)
            self.assertEqual(uri, controller.playlist.tracks[-1].uri)

    def test_add_at_position(self):
        controller = self.backend.current_playlist

        for uri in self.uris[:-1]:
            controller.add(uri, 0)
            self.assertEqual(uri, controller.playlist.tracks[0].uri)

        uri = self.uris[-1]

        controller.add(uri, len(self.uris)+2)
        self.assertEqual(uri, controller.playlist.tracks[-1].uri)

    @populate_playlist
    def test_clear(self):
        controller = self.backend.current_playlist

        controller.clear()

        self.assertEqual(len(controller.playlist.tracks), 0)

    @populate_playlist
    def test_clear_when_playing(self):
        controller = self.backend.current_playlist
        playback = self.backend.playback

        playback.play()

        self.assertEqual(playback.state, playback.PLAYING)

        controller.clear()

        self.assertEqual(playback.state, playback.STOPPED)

    def test_load(self):
        controller = self.backend.current_playlist

        new_playlist = Playlist()

        self.assertNotEqual(new_playlist, controller.playlist)

        controller.load(new_playlist)

        self.assertEqual(new_playlist, controller.playlist)

class BasePlaybackControllerTest(object):
    uris = []
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class()

    def test_play_with_empty_playlist(self):
        playback = self.backend.playback

        self.assertEqual(playback.state, playback.STOPPED)

        result = playback.play()

        self.assertEqual(result, False)
        self.assertEqual(playback.state, playback.STOPPED)

    @populate_playlist
    def test_play(self):
        playback = self.backend.playback

        self.assertEqual(playback.state, playback.STOPPED)

        result = playback.play()

        self.assertEqual(result, True)
        self.assertEqual(playback.state, playback.PLAYING)

    @populate_playlist
    def test_next(self):
        playback = self.backend.playback

        playback.play()

        old_position = playback.playlist_position
        old_uri = playback.current_track.uri

        playback.next()

        self.assertEqual(playback.playlist_position, old_position+1)
        self.assertNotEqual(playback.current_track.uri, old_uri)
