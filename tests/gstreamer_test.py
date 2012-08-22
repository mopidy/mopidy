import sys

from mopidy import settings
from mopidy.gstreamer import GStreamer
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir


@unittest.skipIf(sys.platform == 'win32',
    'Our Windows build server does not support GStreamer yet')
class GStreamerTest(unittest.TestCase):
    def setUp(self):
        settings.BACKENDS = ('mopidy.backends.local.LocalBackend',)
        self.song_uri = path_to_uri(path_to_data_dir('song1.wav'))
        self.gstreamer = GStreamer()
        self.gstreamer.on_start()

    def prepare_uri(self, uri):
        self.gstreamer.prepare_change()
        self.gstreamer.set_uri(uri)

    def tearDown(self):
        settings.runtime.clear()

    def test_start_playback_existing_file(self):
        self.prepare_uri(self.song_uri)
        self.assertTrue(self.gstreamer.start_playback())

    def test_start_playback_non_existing_file(self):
        self.prepare_uri(self.song_uri + 'bogus')
        self.assertFalse(self.gstreamer.start_playback())

    def test_pause_playback_while_playing(self):
        self.prepare_uri(self.song_uri)
        self.gstreamer.start_playback()
        self.assertTrue(self.gstreamer.pause_playback())

    def test_stop_playback_while_playing(self):
        self.prepare_uri(self.song_uri)
        self.gstreamer.start_playback()
        self.assertTrue(self.gstreamer.stop_playback())

    @unittest.SkipTest
    def test_deliver_data(self):
        pass # TODO

    @unittest.SkipTest
    def test_end_of_data_stream(self):
        pass # TODO

    def test_default_get_volume_result(self):
        self.assertEqual(100, self.gstreamer.get_volume())

    def test_set_volume(self):
        self.assertTrue(self.gstreamer.set_volume(50))
        self.assertEqual(50, self.gstreamer.get_volume())

    def test_set_volume_to_zero(self):
        self.assertTrue(self.gstreamer.set_volume(0))
        self.assertEqual(0, self.gstreamer.get_volume())

    def test_set_volume_to_one_hundred(self):
        self.assertTrue(self.gstreamer.set_volume(100))
        self.assertEqual(100, self.gstreamer.get_volume())

    @unittest.SkipTest
    def test_set_state_encapsulation(self):
        pass # TODO

    @unittest.SkipTest
    def test_set_position(self):
        pass # TODO
