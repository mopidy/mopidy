import unittest

from mopidy.backends.dummy import DummyBackend, DummyCurrentPlaylistController
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Playlist, Track

class CurrentPlaylistGetTest(unittest.TestCase):
    def setUp(self):
        self.m = DummyMixer()
        self.b = DummyBackend(mixer=self.m)
        self.c = self.b.current_playlist

    def test_get_by_id_returns_unique_match(self):
        track = Track(id=1)
        self.c.playlist = Playlist(tracks=[Track(id=13), track, Track(id=17)])
        self.assertEqual(track, self.c.get(id=1))

    def test_get_by_id_returns_first_of_multiple_matches(self):
        track = Track(id=1)
        self.c.playlist = Playlist(tracks=[Track(id=13), track, track])
        self.assertEqual(track, self.c.get(id=1))

    def test_get_by_id_raises_keyerror_if_no_match(self):
        self.c.playlist = Playlist(tracks=[Track(id=13), Track(id=17)])
        try:
            self.c.get(id=1)
            self.fail(u'Should raise KeyError if no match')
        except KeyError:
            pass

    def test_get_by_uri_returns_unique_match(self):
        track = Track(uri='a')
        self.c.playlist = Playlist(
            tracks=[Track(uri='z'), track, Track(uri='y')])
        self.assertEqual(track, self.c.get(uri='a'))

    def test_get_by_uri_returns_first_of_multiple_matches(self):
        track = Track(uri='a')
        self.c.playlist = Playlist(tracks=[Track(uri='z'), track, track])
        self.assertEqual(track, self.c.get(uri='a'))

    def test_get_by_uri_raises_keyerror_if_no_match(self):
        self.c.playlist = Playlist(tracks=[Track(uri='z'), Track(uri='y')])
        try:
            self.c.get(uri='a')
            self.fail(u'Should raise KeyError if no match')
        except KeyError as e:
            self.assertEqual(u'Track matching "uri=a" not found', e[0])

    def test_get_by_multiple_criteria_returns_elements_matching_all(self):
        track1 = Track(id=1, uri='a')
        track2 = Track(id=1, uri='b')
        track3 = Track(id=2, uri='b')
        self.c.playlist = Playlist(tracks=[track1, track2, track3])
        self.assertEqual(track1, self.c.get(id=1, uri='a'))
        self.assertEqual(track2, self.c.get(id=1, uri='b'))
        self.assertEqual(track3, self.c.get(id=2, uri='b'))

    def test_get_by_criteria_that_is_not_present_in_all_elements(self):
        track1 = Track(id=1)
        track2 = Track(uri='b')
        track3 = Track(id=2)
        self.c.playlist = Playlist(tracks=[track1, track2, track3])
        self.assertEqual(track1, self.c.get(id=1))
