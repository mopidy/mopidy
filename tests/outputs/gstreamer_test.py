import multiprocessing
import unittest

from tests import SkipTest

# FIXME Our Windows build server does not support GStreamer yet
import sys
if sys.platform == 'win32':
    raise SkipTest

from mopidy import settings
from mopidy.outputs.gstreamer import GStreamerOutput
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir

class GStreamerOutputTest(unittest.TestCase):
    def setUp(self):
        settings.BACKENDS = ('mopidy.backends.local.LocalBackend',)
        self.song_uri = path_to_uri(path_to_data_dir('song1.wav'))
        self.output = GStreamerOutput()
        self.output.on_start()

    def tearDown(self):
        settings.runtime.clear()

    def test_play_uri_existing_file(self):
        self.assertTrue(self.output.play_uri(self.song_uri))

    def test_play_uri_non_existing_file(self):
        self.assertFalse(self.output.play_uri(self.song_uri + 'bogus'))

    @SkipTest
    def test_deliver_data(self):
        pass # TODO

    @SkipTest
    def test_end_of_data_stream(self):
        pass # TODO

    def test_default_get_volume_result(self):
        self.assertEqual(100, self.output.get_volume())

    def test_set_volume(self):
        self.assertTrue(self.output.set_volume(50))
        self.assertEqual(50, self.output.get_volume())

    def test_set_volume_to_zero(self):
        self.assertTrue(self.output.set_volume(0))
        self.assertEqual(0, self.output.get_volume())

    def test_set_volume_to_one_hundred(self):
        self.assertTrue(self.output.set_volume(100))
        self.assertEqual(100, self.output.get_volume())

    @SkipTest
    def test_set_state(self):
        pass # TODO

    @SkipTest
    def test_set_position(self):
        pass # TODO
