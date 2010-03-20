class BaseCurrentPlaylistControllerTest(object):
    uris = []
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class()

    def test_add(self):
        playlist = self.backend.current_playlist

        for uri in self.uris:
            playlist.add(uri)
            self.assertEqual(uri, playlist.tracks[-1].uri)

    def test_add_at_position(self):
        playlist = self.backend.current_playlist

        for uri in self.uris:
            playlist.add(uri, 0)
            self.assertEqual(uri, playlist.tracks[0].uri)

        # FIXME test other placements

class BasePlaybackControllerTest(object):
    backend_class = None

    def setUp(self):
        self.backend = self.backend_class()

    def test_play(self):
        playback = self.backend.playback

        self.assertEqual(playback.state, playback.STOPPED)

        playback.play()

        self.assertEqual(playback.state, playback.PLAYING)

    def test_next(self):
        playback = self.backend.playback

        current_song = playback.playlist_position

        playback.next()

        self.assertEqual(playback.playlist_position, current_song+1)
