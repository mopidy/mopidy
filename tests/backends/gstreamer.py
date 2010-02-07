import unittest

from mopidy.backends.gstreamer import GStreamerBackend

from tests.backends import BasePlaybackControllerTest

class GStreamerPlaybackControllerTest(BasePlaybackControllerTest, unittest.TestCase):
    uri = ['file://data/song1.mp3',
           'file://data/song2.mp3',
           'file://data/song3.mp3',
          ]

    backend_class = GStreamerBackend

if __name__ == '__main__':
    unittest.main()
