import unittest

from mopidy.backends.dummy import DummyBackend, DummyCurrentPlaylistController
from mopidy.models import Playlist, Track

class CurrentPlaylistGetTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend()
        self.c = self.b.current_playlist

    def test_get_by_id_returns_unique_match(self):
        track = Track(id=1)
        self.c.playlist = Playlist(tracks=[Track(id=13), track, Track(id=17)])
        self.assertEqual(track, self.c.get_by_id(1))

    def test_get_by_id_returns_first_of_multiple_matches(self):
        track = Track(id=1)
        self.c.playlist = Playlist(tracks=[Track(id=13), track, track])
        self.assertEqual(track, self.c.get_by_id(1))

    def test_get_by_id_raises_keyerror_if_no_match(self):
        self.c.playlist = Playlist(tracks=[Track(id=13), Track(id=17)])
        try:
            self.c.get_by_id(1)
            self.fail(u'Should raise KeyError if no match')
        except KeyError:
            pass

    def test_get_by_uri_returns_unique_match(self):
        track = Track(uri='a')
        self.c.playlist = Playlist(
            tracks=[Track(uri='z'), track, Track(uri='y')])
        self.assertEqual(track, self.c.get_by_uri('a'))

    def test_get_by_uri_returns_first_of_multiple_matches(self):
        track = Track(uri='a')
        self.c.playlist = Playlist(tracks=[Track(uri='z'), track, track])
        self.assertEqual(track, self.c.get_by_uri('a'))

    def test_get_by_uri_raises_keyerror_if_no_match(self):
        self.c.playlist = Playlist(tracks=[Track(uri='z'), Track(uri='y')])
        try:
            self.c.get_by_uri('a')
            self.fail(u'Should raise KeyError if no match')
        except KeyError:
            pass
