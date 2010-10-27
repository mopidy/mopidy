import unittest
from datetime import date

from mopidy.scanner import Scanner, translator
from mopidy.models import Track, Artist, Album

from tests import data_folder

class FakeGstDate(object):
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

class TranslatorTest(unittest.TestCase):
    def setUp(self):
        self.data = {
            'uri': 'uri',
            'album': u'albumname',
            'track-number': 1,
            'artist': u'name',
            'title': u'trackname',
            'track-count': 2,
            'date': FakeGstDate(2006, 1, 1,),
            'container-format': u'ID3 tag',
            'duration': 4531,
        }

    def test_basic_data(self):
        expected = Track(
            uri='uri',
            name='trackname',
            album=Album(name='albumname', num_tracks=2),
            artists=[Artist(name='name')],
            date=date(2006, 1, 1),
            track_no=1,
            length=4531,
        )
        self.assertEqual(expected, translator(self.data))


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.errors = {}
        self.data = {}

    def scan(self, path):
        scanner = Scanner(data_folder(path),
            self.data_callback, self.error_callback)
        scanner.start()

    def check(self, name, key, value):
        name = data_folder(name)
        self.assertEqual(self.data[name][key], value)

    def data_callback(self, data):
        uri = data['uri'][len('file://'):]
        self.data[uri] = data

    def error_callback(self, uri, errors):
        uri = uri[len('file://'):]
        self.errors[uri] = errors

    def test_data_is_set(self):
        self.scan('scanner/simple')
        self.assert_(self.data)

    def test_errors_is_not_set(self):
        self.scan('scanner/simple')
        self.assert_(not self.errors)

    def test_uri_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'uri', 'file://'
            + data_folder('scanner/simple/song1.mp3'))

    def test_duration_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'duration', 4680)

    def test_artist_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'artist', 'name')

    def test_album_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'album', 'albumname')

    def test_track_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'title', 'trackname')

    def test_other_media_is_ignored(self):
        self.scan('scanner/image')
        self.assert_(self.errors)
