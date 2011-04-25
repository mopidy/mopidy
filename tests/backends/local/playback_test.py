import unittest

# FIXME Our Windows build server does not support GStreamer yet
import sys
if sys.platform == 'win32':
    from tests import SkipTest
    raise SkipTest

from mopidy import settings
from mopidy.backends.local import LocalBackend
from mopidy.models import Track
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir
from tests.backends.base.playback import PlaybackControllerTest
from tests.backends.local import generate_song

class LocalPlaybackControllerTest(PlaybackControllerTest, unittest.TestCase):
    backend_class = LocalBackend
    tracks = [Track(uri=generate_song(i), length=4464)
        for i in range(1, 4)]

    def setUp(self):
        settings.BACKENDS = ('mopidy.backends.local.LocalBackend',)

        super(LocalPlaybackControllerTest, self).setUp()
        # Two tests does not work at all when using the fake sink
        #self.backend.playback.use_fake_sink()

    def tearDown(self):
        super(LocalPlaybackControllerTest, self).tearDown()
        settings.runtime.clear()

    def add_track(self, path):
        uri = path_to_uri(path_to_data_dir(path))
        track = Track(uri=uri, length=4464)
        self.backend.current_playlist.add(track)

    def test_uri_handler(self):
        self.assert_('file://' in self.backend.uri_handlers)

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
