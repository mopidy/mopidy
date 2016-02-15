from __future__ import absolute_import, unicode_literals

import os
import unittest

from mopidy import exceptions
from mopidy.audio import scan
from mopidy.internal import path as path_lib

from tests import path_to_data_dir


class ScannerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.errors = {}
        self.result = {}

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
                self.result[key] = scanner.scan(uri)
            except exceptions.ScannerError as error:
                self.errors[key] = error

    def check(self, name, key, value):
        name = path_to_data_dir(name)
        self.assertEqual(self.result[name].tags[key], value)

    def check_if_missing_plugin(self):
        for path, result in self.result.items():
            if not path.endswith('.mp3'):
                continue
            if not result.playable and result.mime == 'audio/mpeg':
                raise unittest.SkipTest('Missing MP3 support?')

    def test_tags_is_set(self):
        self.scan(self.find('scanner/simple'))
        self.assert_(self.result.values()[0].tags)

    def test_errors_is_not_set(self):
        self.scan(self.find('scanner/simple'))

        self.check_if_missing_plugin()

        self.assert_(not self.errors)

    def test_duration_is_set(self):
        self.scan(self.find('scanner/simple'))

        self.check_if_missing_plugin()

        ogg = path_to_data_dir('scanner/simple/song1.ogg')
        mp3 = path_to_data_dir('scanner/simple/song1.mp3')
        self.assertEqual(self.result[mp3].duration, 4680)
        self.assertEqual(self.result[ogg].duration, 4680)

    def test_artist_is_set(self):
        self.scan(self.find('scanner/simple'))

        self.check_if_missing_plugin()

        self.check('scanner/simple/song1.mp3', 'artist', ['name'])
        self.check('scanner/simple/song1.ogg', 'artist', ['name'])

    def test_album_is_set(self):
        self.scan(self.find('scanner/simple'))

        self.check_if_missing_plugin()

        self.check('scanner/simple/song1.mp3', 'album', ['albumname'])
        self.check('scanner/simple/song1.ogg', 'album', ['albumname'])

    def test_track_is_set(self):
        self.scan(self.find('scanner/simple'))

        self.check_if_missing_plugin()

        self.check('scanner/simple/song1.mp3', 'title', ['trackname'])
        self.check('scanner/simple/song1.ogg', 'title', ['trackname'])

    def test_nonexistant_dir_does_not_fail(self):
        self.scan(self.find('scanner/does-not-exist'))
        self.assert_(not self.errors)

    def test_other_media_is_ignored(self):
        self.scan(self.find('scanner/image'))
        self.assertFalse(self.result.values()[0].playable)

    def test_log_file_that_gst_thinks_is_mpeg_1_is_ignored(self):
        self.scan([path_to_data_dir('scanner/example.log')])

        self.check_if_missing_plugin()

        log = path_to_data_dir('scanner/example.log')
        self.assertLess(self.result[log].duration, 100)

    def test_empty_wav_file(self):
        self.scan([path_to_data_dir('scanner/empty.wav')])
        wav = path_to_data_dir('scanner/empty.wav')
        self.assertEqual(self.result[wav].duration, 0)

    def test_uri_list(self):
        path = path_to_data_dir('scanner/playlist.m3u')
        self.scan([path])
        self.assertEqual(self.result[path].mime, 'text/uri-list')

    def test_text_plain(self):
        # GStreamer decode bin hardcodes bad handling of text plain :/
        path = path_to_data_dir('scanner/plain.txt')
        self.scan([path])
        self.assertIn(path, self.errors)

    @unittest.SkipTest
    def test_song_without_time_is_handeled(self):
        pass
