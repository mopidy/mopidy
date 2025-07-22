import unittest

import pytest

from mopidy import exceptions
from mopidy.internal.path import path_to_uri
from tests import path_to_data_dir


class ScannerTest(unittest.TestCase):
    def setUp(self):
        self.errors = {}
        self.result = {}

    def find(self, path):
        dir_path = path_to_data_dir(path)
        if not dir_path.is_dir():
            return
        for file_path in dir_path.iterdir():
            yield dir_path / file_path

    def scan(self, paths):
        scan = pytest.importorskip(
            "mopidy.audio.gst.scan", reason="test requires GStreamer"
        )
        scanner = scan.Scanner()
        for path in paths:
            uri = path_to_uri(path)
            try:
                self.result[path] = scanner.scan(uri)
            except exceptions.ScannerError as error:
                self.errors[path] = error

    def check(self, name, key, value):
        name = path_to_data_dir(name)
        assert self.result[name].tags[key] == value

    def check_if_missing_plugin(self):
        for path, result in self.result.items():
            if path.suffix != ".mp3":
                continue
            if not result.playable and result.mime == "audio/mpeg":
                msg = "Missing MP3 support?"
                raise unittest.SkipTest(msg)

    def test_tags_is_set(self):
        self.scan(self.find("scanner/simple"))

        assert next(iter(self.result.values())).tags

    def test_errors_is_not_set(self):
        self.scan(self.find("scanner/simple"))

        self.check_if_missing_plugin()

        assert not self.errors

    def test_duration_is_set(self):
        self.scan(self.find("scanner/simple"))

        self.check_if_missing_plugin()

        ogg = path_to_data_dir("scanner/simple/song1.ogg")
        mp3 = path_to_data_dir("scanner/simple/song1.mp3")
        assert self.result[mp3].duration == 4608
        assert self.result[ogg].duration == 4704

    def test_artist_is_set(self):
        self.scan(self.find("scanner/simple"))

        self.check_if_missing_plugin()

        self.check("scanner/simple/song1.mp3", "artist", ["name"])
        self.check("scanner/simple/song1.ogg", "artist", ["name"])

    def test_album_is_set(self):
        self.scan(self.find("scanner/simple"))

        self.check_if_missing_plugin()

        self.check("scanner/simple/song1.mp3", "album", ["albumname"])
        self.check("scanner/simple/song1.ogg", "album", ["albumname"])

    def test_track_is_set(self):
        self.scan(self.find("scanner/simple"))

        self.check_if_missing_plugin()

        self.check("scanner/simple/song1.mp3", "title", ["trackname"])
        self.check("scanner/simple/song1.ogg", "title", ["trackname"])

    def test_nonexistent_dir_does_not_fail(self):
        self.scan(self.find("scanner/does-not-exist"))
        assert not self.errors

    def test_other_media_is_ignored(self):
        self.scan(self.find("scanner/image"))
        assert not next(iter(self.result.values())).playable

    def test_log_file_that_gst_thinks_is_mpeg_1_is_ignored(self):
        self.scan([path_to_data_dir("scanner/example.log")])

        self.check_if_missing_plugin()

        log = path_to_data_dir("scanner/example.log")
        assert self.result[log].duration is None

    def test_empty_wav_file(self):
        self.scan([path_to_data_dir("scanner/empty.wav")])
        wav = path_to_data_dir("scanner/empty.wav")
        assert self.result[wav].duration == 0

    def test_uri_list(self):
        path = path_to_data_dir("scanner/playlist.m3u")
        self.scan([path])
        assert self.result[path].mime == "text/uri-list"

    def test_text_plain(self):
        # GStreamer decode bin hardcodes bad handling of text plain :/
        path = path_to_data_dir("scanner/plain.txt")
        self.scan([path])
        assert path in self.errors

    @unittest.SkipTest
    def test_song_without_time_is_handeled(self):
        pass
