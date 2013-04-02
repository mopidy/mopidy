from __future__ import unicode_literals

from mopidy import settings
from mopidy.backends.local import actor
from mopidy.core import PlaybackState
from mopidy.models import Track
from mopidy.utils.path import path_to_uri

from tests import unittest, path_to_data_dir
from tests.backends.base.playback import PlaybackControllerTest
from tests.backends.local import generate_song


class LocalPlaybackControllerTest(PlaybackControllerTest, unittest.TestCase):
    backend_class = actor.LocalBackend
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]
    # TODO: setup config

    def setUp(self):
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('empty_tag_cache')
        super(LocalPlaybackControllerTest, self).setUp()

    def tearDown(self):
        super(LocalPlaybackControllerTest, self).tearDown()
        settings.runtime.clear()

    def add_track(self, path):
        uri = path_to_uri(path_to_data_dir(path))
        track = Track(uri=uri, length=4464)
        self.tracklist.add([track])

    def test_uri_scheme(self):
        self.assertIn('file', self.core.uri_schemes)

    def test_play_mp3(self):
        self.add_track('blank.mp3')
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    def test_play_ogg(self):
        self.add_track('blank.ogg')
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    def test_play_flac(self):
        self.add_track('blank.flac')
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
