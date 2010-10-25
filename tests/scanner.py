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

    def data_callback(self, uri, data):
        uri = uri.lstrip('file://')
        uri = uri.lstrip(data_folder(''))
        self.data[uri] = data

    def error_callback(self, uri, errors):
        uri = uri.lstrip('file://')
        uri = uri.lstrip(data_folder(''))
        self.errors[uri] = errors

    def test_data_is_set(self):
        self.scan('blank.mp3')
        self.assert_(self.data)

    def test_errors_is_not_set(self):
        self.scan('blank.mp3')
        self.assert_(not self.errors)

    def test_artist_is_set(self):
        self.scan('blank.mp3')
        self.assertEqual(self.data['blank.mp3']['artist'], 'artist')

    def test_album_is_set(self):
        self.scan('blank.mp3')
        self.assertEqual(self.data['blank.mp3']['album'], 'album')

    def test_track_is_set(self):
        self.scan('blank.mp3')
        self.assertEqual(self.data['blank.mp3']['title'], 'title')
