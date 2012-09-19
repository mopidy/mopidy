import sys

from mopidy import audio, settings
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir


@unittest.skipIf(sys.platform == 'win32',
    'Our Windows build server does not support GStreamer yet')
class AudioTest(unittest.TestCase):
    def setUp(self):
        settings.MIXER = 'fakemixer track_max_volume=65536'
        settings.OUTPUT = 'fakesink'
        self.song_uri = path_to_uri(path_to_data_dir('song1.wav'))
        self.audio = audio.Audio.start().proxy()

    def tearDown(self):
        self.audio.stop()
        settings.runtime.clear()

    def prepare_uri(self, uri):
        self.audio.prepare_change()
        self.audio.set_uri(uri)

    def test_start_playback_existing_file(self):
        self.prepare_uri(self.song_uri)
        self.assertTrue(self.audio.start_playback().get())

    def test_start_playback_non_existing_file(self):
        self.prepare_uri(self.song_uri + 'bogus')
        self.assertFalse(self.audio.start_playback().get())

    def test_pause_playback_while_playing(self):
        self.prepare_uri(self.song_uri)
        self.audio.start_playback()
        self.assertTrue(self.audio.pause_playback().get())

    def test_stop_playback_while_playing(self):
        self.prepare_uri(self.song_uri)
        self.audio.start_playback()
        self.assertTrue(self.audio.stop_playback().get())

    @unittest.SkipTest
    def test_deliver_data(self):
        pass # TODO

    @unittest.SkipTest
    def test_end_of_data_stream(self):
        pass # TODO

    def test_set_volume(self):
        for value in range(0, 101):
            self.assertTrue(self.audio.set_volume(value).get())
            self.assertEqual(value, self.audio.get_volume().get())

    @unittest.SkipTest
    def test_set_state_encapsulation(self):
        pass # TODO

    @unittest.SkipTest
    def test_set_position(self):
        pass # TODO

    @unittest.SkipTest
    def test_invalid_output_raises_error(self):
        pass # TODO
