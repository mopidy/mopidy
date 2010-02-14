import unittest

from mopidy.backends.gstreamer import GStreamerBackend

from tests.backends.basetests import (BasePlaybackControllerTest,
                                      BaseCurrentPlaylistControllerTest)

class GStreamerCurrentPlaylistHandlerTest(BaseCurrentPlaylistControllerTest, unittest.TestCase):
    uris = ['file://data/song1.mp3',
            'file://data/song2.mp3',
            'file://data/song3.mp3',
           ]

    backend_class = GStreamerBackend

class GStreamerPlaybackControllerTest(BasePlaybackControllerTest, unittest.TestCase):
    uris = ['file://data/song1.mp3',
            'file://data/song2.mp3',
            'file://data/song3.mp3',
           ]

    backend_class = GStreamerBackend
    supports_volume = True

if __name__ == '__main__':
    unittest.main()
