from __future__ import unicode_literals

import unittest

from mopidy import exceptions
from mopidy.audio import scan
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
            'composer': 'composer',
            'performer': 'performer',
            'album-artist': 'albumartistname',
            'title': 'trackname',
            'track-count': 2,
            'album-disc-number': 2,
            'album-disc-count': 3,
            'date': FakeGstDate(2006, 1, 1,),
            'container-format': 'ID3 tag',
            'genre': 'genre',
            'duration': 4531000000,
            'comment': 'comment',
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

        self.artist_single = {
            'name': 'name',
            'musicbrainz_id': 'mbartistid',
        }

        self.artist_multiple = {
            'name': ['name1', 'name2'],
            'musicbrainz_id': 'mbartistid',
        }

        self.artist = self.artist_single

        self.composer_single = {
            'name': 'composer',
        }

        self.composer_multiple = {
            'name': ['composer1', 'composer2'],
        }

        self.composer = self.composer_single

        self.performer_single = {
            'name': 'performer',
        }

        self.performer_multiple = {
            'name': ['performer1', 'performer2'],
        }

        self.performer = self.performer_single

        self.albumartist = {
            'name': 'albumartistname',
            'musicbrainz_id': 'mbalbumartistid',
        }

        self.track = {
            'uri': 'uri',
            'name': 'trackname',
            'date': '2006-01-01',
            'genre': 'genre',
            'track_no': 1,
            'disc_no': 2,
            'comment': 'comment',
            'length': 4531,
            'musicbrainz_id': 'mbtrackid',
            'last_modified': 1234,
        }

    def build_track(self):
        if self.albumartist:
            self.album['artists'] = [Artist(**self.albumartist)]
        self.track['album'] = Album(**self.album)

        if ('name' in self.artist
                and not isinstance(self.artist['name'], basestring)):
            self.track['artists'] = [Artist(name=artist)
                                     for artist in self.artist['name']]
        else:
            self.track['artists'] = [Artist(**self.artist)]

        if ('name' in self.composer
                and not isinstance(self.composer['name'], basestring)):
            self.track['composers'] = [Artist(name=artist)
                                       for artist in self.composer['name']]
        else:
            self.track['composers'] = [Artist(**self.composer)] \
                if self.composer else ''

        if ('name' in self.performer
                and not isinstance(self.performer['name'], basestring)):
            self.track['performers'] = [Artist(name=artist)
                                        for artist in self.performer['name']]
        else:
            self.track['performers'] = [Artist(**self.performer)] \
                if self.performer else ''

        return Track(**self.track)

    def check(self):
        expected = self.build_track()
        actual = scan.audio_data_to_track(self.data)
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

    def test_missing_composer_name(self):
        del self.data['composer']
        del self.composer['name']
        self.check()

    def test_multiple_track_composers(self):
        self.data['composer'] = ['composer1', 'composer2']
        self.composer = self.composer_multiple
        self.check()

    def test_multiple_track_performers(self):
        self.data['performer'] = ['performer1', 'performer2']
        self.performer = self.performer_multiple
        self.check()

    def test_missing_performer_name(self):
        del self.data['performer']
        del self.performer['name']
        self.check()

    def test_missing_artist_musicbrainz_id(self):
        del self.data['musicbrainz-artistid']
        del self.artist['musicbrainz_id']
        self.check()

    def test_multiple_track_artists(self):
        self.data['artist'] = ['name1', 'name2']
        self.data['musicbrainz-artistid'] = 'mbartistid'
        self.artist = self.artist_multiple
        self.check()

    def test_missing_album_artist(self):
        del self.data['album-artist']
        del self.albumartist['name']
        self.check()

    def test_missing_album_artist_musicbrainz_id(self):
        del self.data['musicbrainz-albumartistid']
        del self.albumartist['musicbrainz_id']
        self.check()

    def test_missing_genre(self):
        del self.data['genre']
        del self.track['genre']
        self.check()

    def test_missing_date(self):
        del self.data['date']
        del self.track['date']
        self.check()

    def test_invalid_date(self):
        self.data['date'] = FakeGstDate(65535, 1, 1)
        del self.track['date']
        self.check()

    def test_missing_comment(self):
        del self.data['comment']
        del self.track['comment']
        self.check()


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.errors = {}
        self.data = {}

    def scan(self, path):
        paths = path_lib.find_files(path_to_data_dir(path))
        uris = (path_lib.path_to_uri(p) for p in paths)
        scanner = scan.Scanner()
        for uri in uris:
            key = uri[len('file://'):]
            try:
                self.data[key] = scanner.scan(uri)
            except exceptions.ScannerError as error:
                self.errors[key] = error

    def check(self, name, key, value):
        name = path_to_data_dir(name)
        self.assertEqual(self.data[name][key], value)

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
        self.check('scanner/simple/song1.mp3', 'duration', 4680000000)
        self.check('scanner/simple/song1.ogg', 'duration', 4680000000)

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

    def test_log_file_that_gst_thinks_is_mpeg_1_is_ignored(self):
        self.scan('scanner/example.log')
        self.assert_(self.errors)

    def test_empty_wav_file_is_ignored(self):
        self.scan('scanner/empty.wav')
        self.assert_(self.errors)

    @unittest.SkipTest
    def test_song_without_time_is_handeled(self):
        pass
