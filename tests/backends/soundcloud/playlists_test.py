# encoding: utf-8

from __future__ import unicode_literals

from mopidy import settings
from mock import patch
from tests import unittest
from mopidy.models import Playlist
from mopidy.backends.soundcloud import soundcloud
from mopidy.backends.soundcloud.playlists import SoundCloudPlaylistsProvider


class SoundCloudClientTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.SOUNDCLOUD_AUTH_TOKEN = '1-11-1111'
        settings.SOUNDCLOUD_EXPLORE = []
        with patch.object(soundcloud.SoundCloudClient, '_get') as get:
            get.return_value.status_code = 200
            get.return_value.content = {'username': 'mopidy', 'user_id': 1}
            cls.sc_api = soundcloud.SoundCloudClient(settings.SOUNDCLOUD_AUTH_TOKEN)
            cls._scp = SoundCloudPlaylistsProvider(backend=cls)

    @classmethod
    def tearDownClass(cls):
        cls._scp = None
        settings.runtime.clear()

    def test_explore_returns_empty(self):

        'create_explore_playlist should return empty tracks,\
         when stream-able is False'
        result = self._scp.create_explore_playlist('mopidy;Love is in the air')
        self.assertIsInstance(result, Playlist)
        self.assertEqual(result.tracks, ())
        self.assertEqual(result.uri, 'soundcloud:exp-mopidy;Love is in the air')
        self.assertEqual(result.name, 'Explore Love is in the air on SoundCloud')

    def test_lookup_sets_returns_tracks(self):

        'lookup must return tracks, when lookup is soundcloud:set-*'
        self._scp._playlists = [Playlist(
            uri='soundcloud:set-love',
            name='Sets',
            tracks=['track1']
        )]
        result = self._scp.lookup('soundcloud:set-love')
        self.assertIsInstance(result, Playlist)
        self.assertEqual(result.tracks, ('track1',))
        self.assertEqual(result.uri, 'soundcloud:set-love')
        self.assertEqual(result.name, 'Sets')
