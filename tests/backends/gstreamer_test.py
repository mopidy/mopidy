import unittest
import os

from mopidy.models import Playlist, Track
from mopidy.backends.gstreamer import GStreamerBackend

from tests.backends.base import (BasePlaybackControllerTest,
                                 BaseCurrentPlaylistControllerTest)

folder = os.path.dirname(__file__)
folder = os.path.join(folder, '..', 'data')
folder = os.path.abspath(folder)
song = os.path.join(folder, 'song%s.wav')
song = 'file://' + song

# FIXME can be switched to generic test
class GStreamerCurrentPlaylistHandlerTest(BaseCurrentPlaylistControllerTest, unittest.TestCase):
    tracks = [Track(uri=song % i, id=i, length=4464) for i in range(1, 4)]

    backend_class = GStreamerBackend

class GStreamerPlaybackControllerTest(BasePlaybackControllerTest, unittest.TestCase):
    tracks = [Track(uri=song % i, id=i, length=4464) for i in range(1, 4)]

    backend_class = GStreamerBackend

    def add_track(self, file):
        uri = 'file://' + os.path.join(folder, file)
        track = Track(uri=uri, id=1, length=4464)
        self.backend.current_playlist.add(track)

    def test_play_mp3(self):
        self.add_track('blank.mp3')
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    def test_play_ogg(self):
        self.add_track('blank.ogg')
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

    def test_play_flac(self):
        self.add_track('blank.flac')
        self.playback.play()
        self.assertEqual(self.playback.state, self.playback.PLAYING)

if __name__ == '__main__':
    unittest.main()
