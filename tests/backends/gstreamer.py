import unittest
import os

from mopidy.backends.gstreamer import GStreamerBackend

from tests.backends.basetests import (BasePlaybackControllerTest,
                                      BaseCurrentPlaylistControllerTest)

folder = os.path.dirname(__file__)
folder = os.path.join(folder, '..', 'data')
folder = os.path.abspath(folder)
song = os.path.join(folder, 'song%s.mp3')
song = 'file://' + song

class GStreamerCurrentPlaylistHandlerTest(BaseCurrentPlaylistControllerTest, unittest.TestCase):
    uris = [song % i for i in range(1, 4)]

    backend_class = GStreamerBackend

class GStreamerPlaybackControllerTest(BasePlaybackControllerTest, unittest.TestCase):
    uris = [song % i for i in range(1, 4)]

    backend_class = GStreamerBackend
    supports_volume = True

if __name__ == '__main__':
    unittest.main()
