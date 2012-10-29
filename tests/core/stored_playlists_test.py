import mock

from mopidy.backends import base
from mopidy.core import Core
from mopidy.models import Playlist, Track

from tests import unittest


class StoredPlaylistsTest(unittest.TestCase):
    def setUp(self):
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.sp1 = mock.Mock(spec=base.BaseStoredPlaylistsProvider)
        self.backend1.stored_playlists = self.sp1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.sp2 = mock.Mock(spec=base.BaseStoredPlaylistsProvider)
        self.backend2.stored_playlists = self.sp2

        self.pl1a = Playlist(tracks=[Track(uri='dummy1:a')])
        self.pl1b = Playlist(tracks=[Track(uri='dummy1:b')])
        self.sp1.playlists.get.return_value = [self.pl1a, self.pl1b]

        self.pl2a = Playlist(tracks=[Track(uri='dummy2:a')])
        self.pl2b = Playlist(tracks=[Track(uri='dummy2:b')])
        self.sp2.playlists.get.return_value = [self.pl2a, self.pl2b]

        self.core = Core(audio=None, backends=[self.backend1, self.backend2])

    def test_get_playlists_combines_result_from_backends(self):
        result = self.core.stored_playlists.playlists

        self.assertIn(self.pl1a, result)
        self.assertIn(self.pl1b, result)
        self.assertIn(self.pl2a, result)
        self.assertIn(self.pl2b, result)

    # TODO The rest of the stored playlists API is pending redesign before
    # we'll update it to support multiple backends.
