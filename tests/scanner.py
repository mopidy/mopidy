import unittest

from mopidy.scanner import Scanner

from tests import data_folder

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

    def data_callback(self, uri, data):
        uri = uri[len('file://'):]
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

    def test_artist_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'artist', 'name')

    def test_album_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'album', 'albumname')

    def test_track_is_set(self):
        self.scan('scanner/simple')
        self.check('scanner/simple/song1.mp3', 'title', 'trackname')
