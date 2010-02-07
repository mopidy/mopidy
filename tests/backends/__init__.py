from mopidy.models import Track

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

class BasePlaybackControllerTest(object):
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class()

    def test_play_with_no_current_track(self):
        playback = self.backend.playback

        self.assertEqual(playback.state, playback.STOPPED)

        result = playback.play()

        self.assertEqual(result, False)
        self.assertEqual(playback.state, playback.STOPPED)

    def test_next(self):
        playback = self.backend.playback

        current_song = playback.playlist_position

        playback.next()

        self.assertEqual(playback.playlist_position, current_song+1)
