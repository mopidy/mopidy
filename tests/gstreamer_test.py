import sys

from mopidy import settings
from mopidy.gstreamer import GStreamer
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir


@unittest.skipIf(sys.platform == 'win32',
    'Our Windows build server does not support GStreamer yet')
class GStreamerTest(unittest.TestCase):
    def setUp(self):
        # TODO: does this modify global settings without reseting it?
        # TODO: should use a fake backend stub for this test?
        settings.BACKENDS = ('mopidy.backends.local.LocalBackend',)
        self.song_uri = path_to_uri(path_to_data_dir('song1.wav'))
        self.gstreamer = GStreamer(mixer='fakemixer track_max_volume=65536')

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

    def test_set_volume(self):
        for value in range(0, 101):
            self.assertTrue(self.gstreamer.set_volume(value))
            self.assertEqual(value, self.gstreamer.get_volume())

    @unittest.SkipTest
    def test_set_state_encapsulation(self):
        pass # TODO

    @unittest.SkipTest
    def test_set_position(self):
        pass # TODO

    @unittest.SkipTest
    def test_invalid_output_raises_error(self):
        pass # TODO

