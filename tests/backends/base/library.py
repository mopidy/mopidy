from __future__ import unicode_literals

import unittest

import pykka

from mopidy import core
from mopidy.models import Track, Album, Artist


class LibraryControllerTest(object):
    artists = [Artist(name='artist1'), Artist(name='artist2'), Artist()]
    albums = [
        Album(name='album1', artists=artists[:1]),
        Album(name='album2', artists=artists[1:2]),
        Album()]
    tracks = [
        Track(uri='local:track:path1', name='track1', artists=artists[:1],
              album=albums[0], date='2001-02-03', length=4000),
        Track(uri='local:track:path2', name='track2', artists=artists[1:2],
              album=albums[1], date='2002', length=4000),
        Track()]
    config = {}

    def setUp(self):
        self.backend = self.backend_class.start(
            config=self.config, audio=None).proxy()
        self.core = core.Core(backends=[self.backend])
        self.library = self.core.library

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_refresh(self):
        self.library.refresh()

    @unittest.SkipTest
    def test_refresh_uri(self):
        pass

    @unittest.SkipTest
    def test_refresh_missing_uri(self):
        pass

    def test_lookup(self):
        tracks = self.library.lookup(self.tracks[0].uri)
        self.assertEqual(tracks, self.tracks[0:1])

    def test_lookup_unknown_track(self):
        tracks = self.library.lookup('fake uri')
        self.assertEqual(tracks, [])

    def test_find_exact_no_hits(self):
        result = self.library.find_exact(track=['unknown track'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(artist=['unknown artist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(album=['unknown artist'])
        self.assertEqual(list(result[0].tracks), [])

    def test_find_exact_uri(self):
        track_1_uri = 'local:track:path1'
        result = self.library.find_exact(uri=track_1_uri)
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        track_2_uri = 'local:track:path2'
        result = self.library.find_exact(uri=track_2_uri)
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_track(self):
        result = self.library.find_exact(track=['track1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(track=['track2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_artist(self):
        result = self.library.find_exact(artist=['artist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(artist=['artist2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_album(self):
        result = self.library.find_exact(album=['album1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(album=['album2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_date(self):
        result = self.library.find_exact(date=['2001'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(date=['2001-02-03'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(date=['2002'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_wrong_type(self):
        test = lambda: self.library.find_exact(wrong=['test'])
        self.assertRaises(LookupError, test)

    def test_find_exact_with_empty_query(self):
        test = lambda: self.library.find_exact(artist=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(track=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(album=[''])
        self.assertRaises(LookupError, test)

    def test_search_no_hits(self):
        result = self.library.search(track=['unknown track'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(artist=['unknown artist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(album=['unknown artist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(uri=['unknown'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(any=['unknown'])
        self.assertEqual(list(result[0].tracks), [])

    def test_search_uri(self):
        result = self.library.search(uri=['TH1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(uri=['TH2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_track(self):
        result = self.library.search(track=['Rack1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(track=['Rack2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_artist(self):
        result = self.library.search(artist=['Tist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(artist=['Tist2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_album(self):
        result = self.library.search(album=['Bum1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(album=['Bum2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_date(self):
        result = self.library.search(date=['2001'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(date=['2001-02-03'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(date=['2001-02-04'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(date=['2002'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_any(self):
        result = self.library.search(any=['Tist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])
        result = self.library.search(any=['Rack1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])
        result = self.library.search(any=['Bum1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])
        result = self.library.search(any=['TH1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

    def test_search_wrong_type(self):
        test = lambda: self.library.search(wrong=['test'])
        self.assertRaises(LookupError, test)

    def test_search_with_empty_query(self):
        test = lambda: self.library.search(artist=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(track=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(album=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(uri=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(any=[''])
        self.assertRaises(LookupError, test)
