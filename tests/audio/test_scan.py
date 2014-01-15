from __future__ import unicode_literals

import os
import unittest

import gobject
gobject.threads_init()

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


# TODO: keep ids without name?
class TranslatorTest(unittest.TestCase):
    def setUp(self):
        self.data = {
            'uri': 'uri',
            'duration': 4531000000,
            'mtime': 1234,
            'tags': {
                'album': ['album'],
                'track-number': [1],
                'artist': ['artist'],
                'composer': ['composer'],
                'performer': ['performer'],
                'album-artist': ['albumartist'],
                'title': ['track'],
                'track-count': [2],
                'album-disc-number': [2],
                'album-disc-count': [3],
                'date': [FakeGstDate(2006, 1, 1,)],
                'container-format': ['ID3 tag'],
                'genre': ['genre'],
                'comment': ['comment'],
                'musicbrainz-trackid': ['trackid'],
                'musicbrainz-albumid': ['albumid'],
                'musicbrainz-artistid': ['artistid'],
                'musicbrainz-albumartistid': ['albumartistid'],
                'bitrate': [1000],
            },
        }

        artist = Artist(name='artist', musicbrainz_id='artistid')
        composer = Artist(name='composer')
        performer = Artist(name='performer')
        albumartist = Artist(name='albumartist',
                             musicbrainz_id='albumartistid')

        album = Album(name='album', num_tracks=2, num_discs=3,
                      musicbrainz_id='albumid', artists=[albumartist])

        self.track = Track(uri='uri', name='track', date='2006-01-01',
                           genre='genre', track_no=1, disc_no=2, length=4531,
                           comment='comment', musicbrainz_id='trackid',
                           last_modified=1234, album=album, bitrate=1000,
                           artists=[artist], composers=[composer],
                           performers=[performer])

    def check(self, expected):
        actual = scan.audio_data_to_track(self.data)
        self.assertEqual(expected, actual)

    def test_track(self):
        self.check(self.track)

    def test_none_track_length(self):
        self.data['duration'] = None
        self.check(self.track.copy(length=None))

    def test_none_track_last_modified(self):
        self.data['mtime'] = None
        self.check(self.track.copy(last_modified=None))

    def test_missing_track_no(self):
        del self.data['tags']['track-number']
        self.check(self.track.copy(track_no=None))

    def test_multiple_track_no(self):
        self.data['tags']['track-number'].append(9)
        self.check(self.track)

    def test_missing_track_disc_no(self):
        del self.data['tags']['album-disc-number']
        self.check(self.track.copy(disc_no=None))

    def test_multiple_track_disc_no(self):
        self.data['tags']['album-disc-number'].append(9)
        self.check(self.track)

    def test_missing_track_name(self):
        del self.data['tags']['title']
        self.check(self.track.copy(name=None))

    def test_multiple_track_name(self):
        self.data['tags']['title'] = ['name1', 'name2']
        self.check(self.track.copy(name='name1; name2'))

    def test_missing_track_musicbrainz_id(self):
        del self.data['tags']['musicbrainz-trackid']
        self.check(self.track.copy(musicbrainz_id=None))

    def test_multiple_track_musicbrainz_id(self):
        self.data['tags']['musicbrainz-trackid'].append('id')
        self.check(self.track)

    def test_missing_track_bitrate(self):
        del self.data['tags']['bitrate']
        self.check(self.track.copy(bitrate=None))

    def test_multiple_track_bitrate(self):
        self.data['tags']['bitrate'].append(1234)
        self.check(self.track)

    def test_missing_track_genre(self):
        del self.data['tags']['genre']
        self.check(self.track.copy(genre=None))

    def test_multiple_track_genre(self):
        self.data['tags']['genre'] = ['genre1', 'genre2']
        self.check(self.track.copy(genre='genre1; genre2'))

    def test_missing_track_date(self):
        del self.data['tags']['date']
        self.check(self.track.copy(date=None))

    def test_multiple_track_date(self):
        self.data['tags']['date'].append(FakeGstDate(2030, 1, 1))
        self.check(self.track)

    def test_invalid_track_date(self):
        self.data['tags']['date'] = [FakeGstDate(65535, 1, 1)]
        self.check(self.track.copy(date=None))

    def test_missing_track_comment(self):
        del self.data['tags']['comment']
        self.check(self.track.copy(comment=None))

    def test_multiple_track_comment(self):
        self.data['tags']['comment'] = ['comment1', 'comment2']
        self.check(self.track.copy(comment='comment1; comment2'))

    def test_missing_track_artist_name(self):
        del self.data['tags']['artist']
        self.check(self.track.copy(artists=[]))

    def test_multiple_track_artist_name(self):
        self.data['tags']['artist'] = ['name1', 'name2']
        artists = [Artist(name='name1'), Artist(name='name2')]
        self.check(self.track.copy(artists=artists))

    def test_missing_track_artist_musicbrainz_id(self):
        del self.data['tags']['musicbrainz-artistid']
        artist = list(self.track.artists)[0].copy(musicbrainz_id=None)
        self.check(self.track.copy(artists=[artist]))

    def test_multiple_track_artist_musicbrainz_id(self):
        self.data['tags']['musicbrainz-artistid'].append('id')
        self.check(self.track)

    def test_missing_track_composer_name(self):
        del self.data['tags']['composer']
        self.check(self.track.copy(composers=[]))

    def test_multiple_track_composer_name(self):
        self.data['tags']['composer'] = ['composer1', 'composer2']
        composers = [Artist(name='composer1'), Artist(name='composer2')]
        self.check(self.track.copy(composers=composers))

    def test_missing_track_performer_name(self):
        del self.data['tags']['performer']
        self.check(self.track.copy(performers=[]))

    def test_multiple_track_performe_name(self):
        self.data['tags']['performer'] = ['performer1', 'performer2']
        performers = [Artist(name='performer1'), Artist(name='performer2')]
        self.check(self.track.copy(performers=performers))

    def test_missing_album_name(self):
        del self.data['tags']['album']
        album = self.track.album.copy(name=None)
        self.check(self.track.copy(album=album))

    def test_multiple_album_name(self):
        self.data['tags']['album'].append('album2')
        self.check(self.track)

    def test_missing_album_musicbrainz_id(self):
        del self.data['tags']['musicbrainz-albumid']
        album = self.track.album.copy(musicbrainz_id=None)
        self.check(self.track.copy(album=album))

    def test_multiple_album_musicbrainz_id(self):
        self.data['tags']['musicbrainz-albumid'].append('id')
        self.check(self.track)

    def test_missing_album_num_tracks(self):
        del self.data['tags']['track-count']
        album = self.track.album.copy(num_tracks=None)
        self.check(self.track.copy(album=album))

    def test_multiple_album_num_tracks(self):
        self.data['tags']['track-count'].append(9)
        self.check(self.track)

    def test_missing_album_num_discs(self):
        del self.data['tags']['album-disc-count']
        album = self.track.album.copy(num_discs=None)
        self.check(self.track.copy(album=album))

    def test_multiple_album_num_discs(self):
        self.data['tags']['album-disc-count'].append(9)
        self.check(self.track)

    def test_missing_album_artist_name(self):
        del self.data['tags']['album-artist']
        album = self.track.album.copy(artists=[])
        self.check(self.track.copy(album=album))

    def test_multiple_album_artist_name(self):
        self.data['tags']['album-artist'] = ['name1', 'name2']
        artists = [Artist(name='name1'), Artist(name='name2')]
        album = self.track.album.copy(artists=artists)
        self.check(self.track.copy(album=album))

    def test_missing_album_artist_musicbrainz_id(self):
        del self.data['tags']['musicbrainz-albumartistid']
        albumartist = list(self.track.album.artists)[0]
        albumartist = albumartist.copy(musicbrainz_id=None)
        album = self.track.album.copy(artists=[albumartist])
        self.check(self.track.copy(album=album))

    def test_multiple_album_artist_musicbrainz_id(self):
        self.data['tags']['musicbrainz-albumartistid'].append('id')
        self.check(self.track)

    def test_stream_organization_track_name(self):
        del self.data['tags']['title']
        self.data['tags']['organization'] = ['organization']
        self.check(self.track.copy(name='organization'))

    def test_multiple_organization_track_name(self):
        del self.data['tags']['title']
        self.data['tags']['organization'] = ['organization1', 'organization2']
        self.check(self.track.copy(name='organization1; organization2'))

    # TODO: combine all comment types?
    def test_stream_location_track_comment(self):
        del self.data['tags']['comment']
        self.data['tags']['location'] = ['location']
        self.check(self.track.copy(comment='location'))

    def test_multiple_location_track_comment(self):
        del self.data['tags']['comment']
        self.data['tags']['location'] = ['location1', 'location2']
        self.check(self.track.copy(comment='location1; location2'))

    def test_stream_copyright_track_comment(self):
        del self.data['tags']['comment']
        self.data['tags']['copyright'] = ['copyright']
        self.check(self.track.copy(comment='copyright'))

    def test_multiple_copyright_track_comment(self):
        del self.data['tags']['comment']
        self.data['tags']['copyright'] = ['copyright1', 'copyright2']
        self.check(self.track.copy(comment='copyright1; copyright2'))


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.errors = {}
        self.data = {}

    def find(self, path):
        media_dir = path_to_data_dir(path)
        for path in path_lib.find_files(media_dir):
            yield os.path.join(media_dir, path)

    def scan(self, paths):
        scanner = scan.Scanner()
        for path in paths:
            uri = path_lib.path_to_uri(path)
            key = uri[len('file://'):]
            try:
                self.data[key] = scanner.scan(uri)
            except exceptions.ScannerError as error:
                self.errors[key] = error

    def check(self, name, key, value):
        name = path_to_data_dir(name)
        self.assertEqual(self.data[name][key], value)

    def check_tag(self, name, key, value):
        name = path_to_data_dir(name)
        self.assertEqual(self.data[name]['tags'][key], value)

    def test_data_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.assert_(self.data)

    def test_errors_is_not_set(self):
        self.scan(self.find('scanner/simple'))
        self.assert_(not self.errors)

    def test_uri_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check(
            'scanner/simple/song1.mp3', 'uri',
            'file://%s' % path_to_data_dir('scanner/simple/song1.mp3'))
        self.check(
            'scanner/simple/song1.ogg', 'uri',
            'file://%s' % path_to_data_dir('scanner/simple/song1.ogg'))

    def test_duration_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check('scanner/simple/song1.mp3', 'duration', 4680000000)
        self.check('scanner/simple/song1.ogg', 'duration', 4680000000)

    def test_artist_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check_tag('scanner/simple/song1.mp3', 'artist', ['name'])
        self.check_tag('scanner/simple/song1.ogg', 'artist', ['name'])

    def test_album_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check_tag('scanner/simple/song1.mp3', 'album', ['albumname'])
        self.check_tag('scanner/simple/song1.ogg', 'album', ['albumname'])

    def test_track_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check_tag('scanner/simple/song1.mp3', 'title', ['trackname'])
        self.check_tag('scanner/simple/song1.ogg', 'title', ['trackname'])

    def test_nonexistant_dir_does_not_fail(self):
        self.scan(self.find('scanner/does-not-exist'))
        self.assert_(not self.errors)

    def test_other_media_is_ignored(self):
        self.scan(self.find('scanner/image'))
        self.assert_(self.errors)

    def test_log_file_that_gst_thinks_is_mpeg_1_is_ignored(self):
        self.scan([path_to_data_dir('scanner/example.log')])
        self.assert_(self.errors)

    def test_empty_wav_file_is_ignored(self):
        self.scan([path_to_data_dir('scanner/empty.wav')])
        self.assert_(self.errors)

    @unittest.SkipTest
    def test_song_without_time_is_handeled(self):
        pass
