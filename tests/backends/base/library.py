from mopidy.models import Playlist, Track, Album, Artist

from tests import unittest, path_to_data_dir


class LibraryControllerTest(object):
    artists = [Artist(name='artist1'), Artist(name='artist2'), Artist()]
    albums = [Album(name='album1', artists=artists[:1]),
        Album(name='album2', artists=artists[1:2]),
        Album()]
    tracks = [Track(name='track1', length=4000, artists=artists[:1],
            album=albums[0], uri='file://' + path_to_data_dir('uri1')),
        Track(name='track2', length=4000, artists=artists[1:2],
            album=albums[1], uri='file://' + path_to_data_dir('uri2')),
        Track()]

    def setUp(self):
        self.backend = self.backend_class()
        self.library = self.backend.library

    def test_refresh(self):
        self.library.refresh()

    @unittest.SkipTest
    def test_refresh_uri(self):
        pass

    @unittest.SkipTest
    def test_refresh_missing_uri(self):
        pass

    def test_lookup(self):
        track = self.library.lookup(self.tracks[0].uri)
        self.assertEqual(track, self.tracks[0])

    def test_lookup_unknown_track(self):
        test = lambda: self.library.lookup('fake uri')
        self.assertRaises(LookupError, test)

    def test_find_exact_no_hits(self):
        result = self.library.find_exact(track=['unknown track'])
        self.assertEqual(result, Playlist())

        result = self.library.find_exact(artist=['unknown artist'])
        self.assertEqual(result, Playlist())

        result = self.library.find_exact(album=['unknown artist'])
        self.assertEqual(result, Playlist())

    def test_find_exact_artist(self):
        result = self.library.find_exact(artist=['artist1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.find_exact(artist=['artist2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_find_exact_track(self):
        result = self.library.find_exact(track=['track1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.find_exact(track=['track2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_find_exact_album(self):
        result = self.library.find_exact(album=['album1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.find_exact(album=['album2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

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
        self.assertEqual(result, Playlist())

        result = self.library.search(artist=['unknown artist'])
        self.assertEqual(result, Playlist())

        result = self.library.search(album=['unknown artist'])
        self.assertEqual(result, Playlist())

        result = self.library.search(uri=['unknown'])
        self.assertEqual(result, Playlist())

        result = self.library.search(any=['unknown'])
        self.assertEqual(result, Playlist())

    def test_search_artist(self):
        result = self.library.search(artist=['Tist1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search(artist=['Tist2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_track(self):
        result = self.library.search(track=['Rack1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search(track=['Rack2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_album(self):
        result = self.library.search(album=['Bum1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search(album=['Bum2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_uri(self):
        result = self.library.search(uri=['RI1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

        result = self.library.search(uri=['RI2'])
        self.assertEqual(result, Playlist(tracks=self.tracks[1:2]))

    def test_search_any(self):
        result = self.library.search(any=['Tist1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))
        result = self.library.search(any=['Rack1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))
        result = self.library.search(any=['Bum1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))
        result = self.library.search(any=['RI1'])
        self.assertEqual(result, Playlist(tracks=self.tracks[:1]))

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
