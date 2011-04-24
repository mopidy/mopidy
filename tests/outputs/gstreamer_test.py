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

    def test_build_shoutcast_description_without_server(self):
        self.assertEqual(None, self.output._build_shoutcast_description())

    def test_build_shoutcast_description_with_server(self):
        settings.SHOUTCAST_SERVER = '127.0.0.1'

        expected = u'%s ! ' % settings.SHOUTCAST_ENCODER + \
            u'shout2send ip="127.0.0.1" mount="/stream" ' \
            u'password="hackme" port="8000" username="source"'
        result = self.output._build_shoutcast_description()
        self.assertEqual(expected, result)

    def test_build_shoutcast_description_with_mount(self):
        settings.SHOUTCAST_SERVER = '127.0.0.1'
        settings.SHOUTCAST_MOUNT = '/stream.mp3'

        expected = u'%s ! ' % settings.SHOUTCAST_ENCODER + \
            u'shout2send ip="127.0.0.1" mount="/stream.mp3" ' \
            u'password="hackme" port="8000" username="source"'
        result = self.output._build_shoutcast_description()
        self.assertEqual(expected, result)

    def test_build_shoutcast_description_with_user_and_passwod(self):
        settings.SHOUTCAST_SERVER = '127.0.0.1'
        settings.SHOUTCAST_USER = 'john'
        settings.SHOUTCAST_PASSWORD = 'doe'

        expected = u'%s ! ' % settings.SHOUTCAST_ENCODER + \
            u'shout2send ip="127.0.0.1" mount="/stream" ' \
            u'password="doe" port="8000" username="john"'
        result = self.output._build_shoutcast_description()
        self.assertEqual(expected, result)

    def test_build_shoutcast_description_unset_user_and_pass(self):
        settings.SHOUTCAST_SERVER = '127.0.0.1'
        settings.SHOUTCAST_USER = None
        settings.SHOUTCAST_PASSWORD = None

        expected = u'%s ! shout2send ' % settings.SHOUTCAST_ENCODER + \
            u'ip="127.0.0.1" mount="/stream" port="8000"'
        result = self.output._build_shoutcast_description()
        self.assertEqual(expected, result)

    def test_build_shoutcast_description_with_override(self):
        settings.SHOUTCAST_OVERRIDE = 'foobar'

        result = self.output._build_shoutcast_description()
        self.assertEqual('foobar', result)

    def test_build_shoutcast_description_with_override_and_server(self):
        settings.SHOUTCAST_OVERRIDE = 'foobar'
        settings.SHOUTCAST_SERVER = '127.0.0.1'

        result = self.output._build_shoutcast_description()
        self.assertEqual('foobar', result)
