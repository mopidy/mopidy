from __future__ import unicode_literals

import unittest

from mopidy.backends.local import actor
from mopidy.core import PlaybackState
from mopidy.models import Track

from tests import path_to_data_dir
from tests.backends.base.playback import PlaybackControllerTest
from tests.backends.local import generate_song


class LocalPlaybackControllerTest(PlaybackControllerTest, unittest.TestCase):
    backend_class = actor.LocalBackend
    config = {
        'local': {
            'media_dir': path_to_data_dir(''),
            'playlists_dir': b'',
            'tag_cache_file': path_to_data_dir('empty_tag_cache'),
        }
    }
    tracks = [
        Track(uri=generate_song(i), length=4464) for i in range(1, 4)]

    def add_track(self, uri):
        track = Track(uri=uri, length=4464)
        self.tracklist.add([track])

    def test_uri_scheme(self):
        self.assertNotIn('file', self.core.uri_schemes)
        self.assertIn('local', self.core.uri_schemes)

    def test_play_mp3(self):
        self.add_track('local:track:blank.mp3')
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    def test_play_ogg(self):
        self.add_track('local:track:blank.ogg')
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)

    def test_play_flac(self):
        self.add_track('local:track:blank.flac')
        self.playback.play()
        self.assertEqual(self.playback.state, PlaybackState.PLAYING)
