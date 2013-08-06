from __future__ import unicode_literals

import unittest

from mopidy.scanner import Scanner, translator
from mopidy.models import Track, Artist, Album
from mopidy.utils import path as path_lib

from tests import path_to_data_dir


class FakeGstDate(object):
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day


class TranslatorTest(unittest.TestCase):
    def setUp(self):
        self.data = {
            'uri': 'uri',
            'album': 'albumname',
            'track-number': 1,
            'artist': 'name',
            'album-artist': 'albumartistname',
            'title': 'trackname',
            'track-count': 2,
            'album-disc-number': 2,
            'album-disc-count': 3,
            'date': FakeGstDate(2006, 1, 1,),
            'container-format': 'ID3 tag',
            'duration': 4531,
            'musicbrainz-trackid': 'mbtrackid',
            'musicbrainz-albumid': 'mbalbumid',
            'musicbrainz-artistid': 'mbartistid',
            'musicbrainz-albumartistid': 'mbalbumartistid',
            'mtime': 1234,
        }

        self.album = {
            'name': 'albumname',
            'num_tracks': 2,
            'num_discs': 3,
            'musicbrainz_id': 'mbalbumid',
        }

        self.artist = {
            'name': 'name',
            'musicbrainz_id': 'mbartistid',
        }

        self.albumartist = {
            'name': 'albumartistname',
            'musicbrainz_id': 'mbalbumartistid',
        }

        self.track = {
            'uri': 'uri',
            'name': 'trackname',
            'date': '2006-01-01',
            'track_no': 1,
            'disc_no': 2,
            'length': 4531,
            'musicbrainz_id': 'mbtrackid',
            'last_modified': 1234,
        }

    def build_track(self):
        if self.albumartist:
            self.album['artists'] = [Artist(**self.albumartist)]
        self.track['album'] = Album(**self.album)
        self.track['artists'] = [Artist(**self.artist)]
        return Track(**self.track)

    def check(self):
        expected = self.build_track()
        actual = translator(self.data)
        self.assertEqual(expected, actual)

    def test_basic_data(self):
        self.check()

    def test_missing_track_number(self):
        del self.data['track-number']
        del self.track['track_no']
        self.check()

    def test_missing_track_count(self):
        del self.data['track-count']
        del self.album['num_tracks']
        self.check()

    def test_missing_track_name(self):
        del self.data['title']
        del self.track['name']
        self.check()

    def test_missing_track_musicbrainz_id(self):
        del self.data['musicbrainz-trackid']
        del self.track['musicbrainz_id']
        self.check()

    def test_missing_album_name(self):
        del self.data['album']
        del self.album['name']
        self.check()

    def test_missing_album_musicbrainz_id(self):
        del self.data['musicbrainz-albumid']
        del self.album['musicbrainz_id']
        self.check()

    def test_missing_artist_name(self):
        del self.data['artist']
        del self.artist['name']
        self.check()

    def test_missing_artist_musicbrainz_id(self):
        del self.data['musicbrainz-artistid']
        del self.artist['musicbrainz_id']
        self.check()

    def test_missing_album_artist(self):
        del self.data['album-artist']
        del self.albumartist['name']
        self.check()

    def test_missing_album_artist_musicbrainz_id(self):
        del self.data['musicbrainz-albumartistid']
        del self.albumartist['musicbrainz_id']
        self.check()

    def test_missing_date(self):
        del self.data['date']
        del self.track['date']
        self.check()

    def test_invalid_date(self):
        self.data['date'] = FakeGstDate(65535, 1, 1)
        del self.track['date']
        self.check()


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.errors = {}
        self.data = {}

    def scan(self, path):
        paths = path_lib.find_files(path_to_data_dir(path))
        uris = (path_lib.path_to_uri(p) for p in paths)
        scanner = Scanner(uris, self.data_callback, self.error_callback)
        scanner.start()

    def check(self, name, key, value):
        name = path_to_data_dir(name)
        self.assertEqual(self.data[name][key], value)

    def data_callback(self, data):
        uri = data['uri'][len('file://'):]
        self.data[uri] = data

    def error_callback(self, uri, error, debug):
        uri = uri[len('file://'):]
        self.errors[uri] = (error, debug)

    def test_data_is_set(self):
        self.scan('scanner/simple')
        self.assert_(self.data)

    def test_errors_is_not_set(self):
        self.scan('scanner/simple')
        self.assert_(not self.errors)

    def test_uri_is_set(self):
        self.scan('scanner/simple')
        self.check(
            'scanner/simple/song1.mp3', 'uri',
            'file://%s' % path_to_data_dir('scanner/simple/song1.mp3'))
        self.check(
            'scanner/simple/song1.ogg', 'uri',
            'file://%s' % path_to_data_dir('scanner/simple/song1.ogg'))

    def test_duration_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'duration', 4680)
        self.check('scanner/simple/song1.ogg', 'duration', 4680)

    def test_artist_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'artist', 'name')
        self.check('scanner/simple/song1.ogg', 'artist', 'name')

    def test_album_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'album', 'albumname')
        self.check('scanner/simple/song1.ogg', 'album', 'albumname')

    def test_track_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'title', 'trackname')
        self.check('scanner/simple/song1.ogg', 'title', 'trackname')

    def test_nonexistant_dir_does_not_fail(self):
        self.scan('scanner/does-not-exist')
        self.assert_(not self.errors)

    def test_other_media_is_ignored(self):
        self.scan('scanner/image')
        self.assert_(self.errors)

    def test_log_file_is_ignored(self):
        self.scan('scanner/example.log')
        self.assert_(self.errors)

    def test_empty_wav_file_is_ignored(self):
        self.scan('scanner/empty.wav')
        self.assert_(self.errors)

    @unittest.SkipTest
    def test_song_without_time_is_handeled(self):
        pass
