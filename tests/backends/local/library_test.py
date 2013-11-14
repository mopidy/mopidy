from __future__ import unicode_literals

import tempfile
import unittest

import pykka

from mopidy import core
from mopidy.backends.local import actor
from mopidy.models import Track, Album, Artist

from tests import path_to_data_dir


# TODO: update tests to only use backend, not core. we need a seperate
# core test that does this integration test.
class LocalLibraryProviderTest(unittest.TestCase):
    artists = [
        Artist(name='artist1'),
        Artist(name='artist2'),
        Artist(name='artist3'),
        Artist(name='artist4'),
        Artist(name='artist5'),
        Artist(name='artist6'),
    ]

    albums = [
        Album(name='album1', artists=[artists[0]]),
        Album(name='album2', artists=[artists[1]]),
        Album(name='album3', artists=[artists[2]]),
        Album(name='album4'),
    ]

    tracks = [
        Track(
            uri='local:track:path1', name='track1',
            artists=[artists[0]], album=albums[0],
            date='2001-02-03', length=4000, track_no=1),
        Track(
            uri='local:track:path2', name='track2',
            artists=[artists[1]], album=albums[1],
            date='2002', length=4000, track_no=2),
        Track(
            uri='local:track:path3', name='track3',
            artists=[artists[3]], album=albums[2],
            date='2003', length=4000, track_no=3),
        Track(
            uri='local:track:path4', name='track4',
            artists=[artists[2]], album=albums[3],
            date='2004', length=60000, track_no=4,
            comment='This is a fantastic track'),
        Track(
            uri='local:track:path5', name='track5', genre='genre1',
            album=albums[3], length=4000, composers=[artists[4]]),
        Track(
            uri='local:track:path6', name='track6', genre='genre2',
            album=albums[3], length=4000, performers=[artists[5]]),
    ]

    config = {
        'local': {
            'media_dir': path_to_data_dir(''),
            'playlists_dir': b'',
            'tag_cache_file': path_to_data_dir('library_tag_cache'),
        }
    }

    def setUp(self):
        self.backend = actor.LocalBackend.start(
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

    def test_refresh_missing_uri(self):
        # Verifies that https://github.com/mopidy/mopidy/issues/500
        # has been fixed.

        tag_cache = tempfile.NamedTemporaryFile()
        with open(self.config['local']['tag_cache_file']) as fh:
            tag_cache.write(fh.read())
        tag_cache.flush()

        config = {'local': self.config['local'].copy()}
        config['local']['tag_cache_file'] = tag_cache.name
        backend = actor.LocalBackend(config=config, audio=None)

        # Sanity check that value is in tag cache
        result = backend.library.lookup(self.tracks[0].uri)
        self.assertEqual(result, self.tracks[0:1])

        # Clear tag cache and refresh
        tag_cache.seek(0)
        tag_cache.truncate()
        backend.library.refresh()

        # Now it should be gone.
        result = backend.library.lookup(self.tracks[0].uri)
        self.assertEqual(result, [])

    def test_lookup(self):
        tracks = self.library.lookup(self.tracks[0].uri)
        self.assertEqual(tracks, self.tracks[0:1])

    def test_lookup_unknown_track(self):
        tracks = self.library.lookup('fake uri')
        self.assertEqual(tracks, [])

    def test_find_exact_no_hits(self):
        result = self.library.find_exact(track_name=['unknown track'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(artist=['unknown artist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(albumartist=['unknown albumartist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(composer=['unknown composer'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(performer=['unknown performer'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(album=['unknown album'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(date=['1990'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(genre=['unknown genre'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(track_no=['9'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(track_no=['no_match'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(comment=['fake comment'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(uri=['fake uri'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(any=['unknown any'])
        self.assertEqual(list(result[0].tracks), [])

    def test_find_exact_uri(self):
        track_1_uri = 'local:track:path1'
        result = self.library.find_exact(uri=track_1_uri)
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        track_2_uri = 'local:track:path2'
        result = self.library.find_exact(uri=track_2_uri)
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_track_name(self):
        result = self.library.find_exact(track_name=['track1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(track_name=['track2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_artist(self):
        result = self.library.find_exact(artist=['artist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(artist=['artist2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

        result = self.library.find_exact(artist=['artist3'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

    def test_find_exact_composer(self):
        result = self.library.find_exact(composer=['artist5'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        result = self.library.find_exact(composer=['artist6'])
        self.assertEqual(list(result[0].tracks), [])

    def test_find_exact_performer(self):
        result = self.library.find_exact(performer=['artist6'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

        result = self.library.find_exact(performer=['artist5'])
        self.assertEqual(list(result[0].tracks), [])

    def test_find_exact_album(self):
        result = self.library.find_exact(album=['album1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(album=['album2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_albumartist(self):
        # Artist is both track artist and album artist
        result = self.library.find_exact(albumartist=['artist1'])
        self.assertEqual(list(result[0].tracks), [self.tracks[0]])

        # Artist is both track and album artist
        result = self.library.find_exact(albumartist=['artist2'])
        self.assertEqual(list(result[0].tracks), [self.tracks[1]])

        # Artist is just album artist
        result = self.library.find_exact(albumartist=['artist3'])
        self.assertEqual(list(result[0].tracks), [self.tracks[2]])

    def test_find_exact_track_no(self):
        result = self.library.find_exact(track_no=['1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(track_no=['2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_genre(self):
        result = self.library.find_exact(genre=['genre1'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        result = self.library.find_exact(genre=['genre2'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

    def test_find_exact_date(self):
        result = self.library.find_exact(date=['2001'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.find_exact(date=['2001-02-03'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(date=['2002'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_find_exact_comment(self):
        result = self.library.find_exact(
            comment=['This is a fantastic track'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

        result = self.library.find_exact(
            comment=['This is a fantastic'])
        self.assertEqual(list(result[0].tracks), [])

    def test_find_exact_any(self):
        # Matches on track artist
        result = self.library.find_exact(any=['artist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(any=['artist2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

        # Matches on track name
        result = self.library.find_exact(any=['track1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.find_exact(any=['track2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

        # Matches on track album
        result = self.library.find_exact(any=['album1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        # Matches on track album artists
        result = self.library.find_exact(any=['artist3'])
        self.assertEqual(
            list(result[0].tracks), [self.tracks[3], self.tracks[2]])

        # Matches on track composer
        result = self.library.find_exact(any=['artist5'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        # Matches on track performer
        result = self.library.find_exact(any=['artist6'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

        # Matches on track genre
        result = self.library.find_exact(any=['genre1'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        result = self.library.find_exact(any=['genre2'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

        # Matches on track date
        result = self.library.find_exact(any=['2002'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

        # Matches on track comment
        result = self.library.find_exact(
            any=['This is a fantastic track'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

        # Matches on URI
        result = self.library.find_exact(any=['local:track:path1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

    def test_find_exact_wrong_type(self):
        test = lambda: self.library.find_exact(wrong=['test'])
        self.assertRaises(LookupError, test)

    def test_find_exact_with_empty_query(self):
        test = lambda: self.library.find_exact(artist=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(albumartist=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(track_name=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(composer=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(performer=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(album=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(track_no=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(genre=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(date=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(comment=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.find_exact(any=[''])
        self.assertRaises(LookupError, test)

    def test_search_no_hits(self):
        result = self.library.search(track_name=['unknown track'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(artist=['unknown artist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(albumartist=['unknown albumartist'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(composer=['unknown composer'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(performer=['unknown performer'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(album=['unknown album'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(track_no=['9'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(track_no=['no_match'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(genre=['unknown genre'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(date=['unknown date'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(comment=['unknown comment'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(uri=['unknown uri'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(any=['unknown anything'])
        self.assertEqual(list(result[0].tracks), [])

    def test_search_uri(self):
        result = self.library.search(uri=['TH1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(uri=['TH2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_track_name(self):
        result = self.library.search(track_name=['Rack1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(track_name=['Rack2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_artist(self):
        result = self.library.search(artist=['Tist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(artist=['Tist2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_albumartist(self):
        # Artist is both track artist and album artist
        result = self.library.search(albumartist=['Tist1'])
        self.assertEqual(list(result[0].tracks), [self.tracks[0]])

        # Artist is both track artist and album artist
        result = self.library.search(albumartist=['Tist2'])
        self.assertEqual(list(result[0].tracks), [self.tracks[1]])

        # Artist is just album artist
        result = self.library.search(albumartist=['Tist3'])
        self.assertEqual(list(result[0].tracks), [self.tracks[2]])

    def test_search_composer(self):
        result = self.library.search(composer=['Tist5'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

    def test_search_performer(self):
        result = self.library.search(performer=['Tist6'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

    def test_search_album(self):
        result = self.library.search(album=['Bum1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(album=['Bum2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_genre(self):
        result = self.library.search(genre=['Enre1'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        result = self.library.search(genre=['Enre2'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

    def test_search_date(self):
        result = self.library.search(date=['2001'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(date=['2001-02-03'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(date=['2001-02-04'])
        self.assertEqual(list(result[0].tracks), [])

        result = self.library.search(date=['2002'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_track_no(self):
        result = self.library.search(track_no=['1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(track_no=['2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

    def test_search_comment(self):
        result = self.library.search(comment=['fantastic'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

        result = self.library.search(comment=['antasti'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

    def test_search_any(self):
        # Matches on track artist
        result = self.library.search(any=['Tist1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        # Matches on track composer
        result = self.library.search(any=['Tist5'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        # Matches on track performer
        result = self.library.search(any=['Tist6'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

        # Matches on track
        result = self.library.search(any=['Rack1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        result = self.library.search(any=['Rack2'])
        self.assertEqual(list(result[0].tracks), self.tracks[1:2])

        # Matches on track album
        result = self.library.search(any=['Bum1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

        # Matches on track album artists
        result = self.library.search(any=['Tist3'])
        self.assertEqual(
            list(result[0].tracks), [self.tracks[3], self.tracks[2]])

        # Matches on track genre
        result = self.library.search(any=['Enre1'])
        self.assertEqual(list(result[0].tracks), self.tracks[4:5])

        result = self.library.search(any=['Enre2'])
        self.assertEqual(list(result[0].tracks), self.tracks[5:6])

        # Matches on track comment
        result = self.library.search(any=['fanta'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

        result = self.library.search(any=['is a fan'])
        self.assertEqual(list(result[0].tracks), self.tracks[3:4])

        # Matches on URI
        result = self.library.search(any=['TH1'])
        self.assertEqual(list(result[0].tracks), self.tracks[:1])

    def test_search_wrong_type(self):
        test = lambda: self.library.search(wrong=['test'])
        self.assertRaises(LookupError, test)

    def test_search_with_empty_query(self):
        test = lambda: self.library.search(artist=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(albumartist=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(composer=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(performer=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(track_name=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(album=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(genre=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(date=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(comment=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(uri=[''])
        self.assertRaises(LookupError, test)

        test = lambda: self.library.search(any=[''])
        self.assertRaises(LookupError, test)
