from __future__ import absolute_import, unicode_literals

import os
import unittest

import gobject
gobject.threads_init()

from mopidy import exceptions
from mopidy.audio import scan
from mopidy.utils import path as path_lib

from tests import path_to_data_dir


class ScannerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.errors = {}
        self.tags = {}
        self.durations = {}

    def find(self, path):
        media_dir = path_to_data_dir(path)
        result, errors = path_lib.find_mtimes(media_dir)
        for path in result:
            yield os.path.join(media_dir, path)

    def scan(self, paths):
        scanner = scan.Scanner()
        for path in paths:
            uri = path_lib.path_to_uri(path)
            key = uri[len('file://'):]
            try:
                result = scanner.scan(uri)
                self.tags[key] = result.tags
                self.durations[key] = result.duration
            except exceptions.ScannerError as error:
                self.errors[key] = error

    def check(self, name, key, value):
        name = path_to_data_dir(name)
        self.assertEqual(self.tags[name][key], value)

    def test_tags_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.assert_(self.tags)

    def test_errors_is_not_set(self):
        self.scan(self.find('scanner/simple'))
        self.assert_(not self.errors)

    def test_duration_is_set(self):
        self.scan(self.find('scanner/simple'))

        self.assertEqual(
            self.durations[path_to_data_dir('scanner/simple/song1.mp3')], 4680)
        self.assertEqual(
            self.durations[path_to_data_dir('scanner/simple/song1.ogg')], 4680)

    def test_artist_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check('scanner/simple/song1.mp3', 'artist', ['name'])
        self.check('scanner/simple/song1.ogg', 'artist', ['name'])

    def test_album_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check('scanner/simple/song1.mp3', 'album', ['albumname'])
        self.check('scanner/simple/song1.ogg', 'album', ['albumname'])

    def test_track_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.check('scanner/simple/song1.mp3', 'title', ['trackname'])
        self.check('scanner/simple/song1.ogg', 'title', ['trackname'])

    def test_nonexistant_dir_does_not_fail(self):
        self.scan(self.find('scanner/does-not-exist'))
        self.assert_(not self.errors)

    def test_other_media_is_ignored(self):
        self.scan(self.find('scanner/image'))
        self.assert_(self.errors)

    def test_log_file_that_gst_thinks_is_mpeg_1_is_ignored(self):
        self.scan([path_to_data_dir('scanner/example.log')])
        self.assertLess(
            self.durations[path_to_data_dir('scanner/example.log')], 100)

    def test_empty_wav_file(self):
        self.scan([path_to_data_dir('scanner/empty.wav')])
        self.assertEqual(
            self.durations[path_to_data_dir('scanner/empty.wav')], 0)

    @unittest.SkipTest
    def test_song_without_time_is_handeled(self):
        pass
