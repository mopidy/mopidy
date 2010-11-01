# encoding: utf-8

import os
import tempfile
import unittest

from mopidy.utils.path import path_to_uri
from mopidy.backends.local.translator import parse_m3u, parse_mpd_tag_cache
from mopidy.models import Track, Artist, Album

from tests import SkipTest, data_folder

song1_path = data_folder('song1.mp3')
song2_path = data_folder('song2.mp3')
encoded_path = data_folder(u'æøå.mp3')
song1_uri = path_to_uri(song1_path)
song2_uri = path_to_uri(song2_path)
encoded_uri = path_to_uri(encoded_path)

class M3UToUriTest(unittest.TestCase):
    def test_empty_file(self):
        uris = parse_m3u(data_folder('empty.m3u'))
        self.assertEqual([], uris)

    def test_basic_file(self):
        uris = parse_m3u(data_folder('one.m3u'))
        self.assertEqual([song1_uri], uris)

    def test_file_with_comment(self):
        uris = parse_m3u(data_folder('comment.m3u'))
        self.assertEqual([song1_uri], uris)

    def test_file_with_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path)
        try:
            uris = parse_m3u(tmp.name)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_multiple_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path+'\n')
            tmp.write('# comment \n')
            tmp.write(song2_path)
        try:
            uris = parse_m3u(tmp.name)
            self.assertEqual([song1_uri, song2_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)


    def test_file_with_uri(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_uri)
        try:
            uris = parse_m3u(tmp.name)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_encoding_is_latin1(self):
        uris = parse_m3u(data_folder('encoding.m3u'))
        self.assertEqual([encoded_uri], uris)

    def test_open_missing_file(self):
        uris = parse_m3u(data_folder('non-existant.m3u'))
        self.assertEqual([], uris)


class URItoM3UTest(unittest.TestCase):
    pass

expected_artists = [Artist(name='name')]
expected_albums = [Album(name='albumname', artists=expected_artists,
    num_tracks=2)]
expected_tracks = []

def generate_track(path, ident):
    uri = path_to_uri(data_folder(path))
    track = Track(name='trackname', artists=expected_artists, track_no=1,
        album=expected_albums[0], length=4000, uri=uri)
    expected_tracks.append(track)

generate_track('song1.mp3', 6)
generate_track('song2.mp3', 7)
generate_track('song3.mp3', 8)
generate_track('subdir1/song4.mp3', 2)
generate_track('subdir1/song5.mp3', 3)
generate_track('subdir2/song6.mp3', 4)
generate_track('subdir2/song7.mp3', 5)
generate_track('subdir1/subsubdir/song8.mp3', 0)
generate_track('subdir1/subsubdir/song9.mp3', 1)

class MPDTagCacheToTracksTest(unittest.TestCase):
    def test_emtpy_cache(self):
        tracks = parse_mpd_tag_cache(data_folder('empty_tag_cache'),
            data_folder(''))
        self.assertEqual(set(), tracks)

    def test_simple_cache(self):
        tracks = parse_mpd_tag_cache(data_folder('simple_tag_cache'),
            data_folder(''))
        uri = path_to_uri(data_folder('song1.mp3'))
        track = Track(name='trackname', artists=expected_artists, track_no=1,
            album=expected_albums[0], length=4000, uri=uri)
        self.assertEqual(set([track]), tracks)

    def test_advanced_cache(self):
        tracks = parse_mpd_tag_cache(data_folder('advanced_tag_cache'),
             data_folder(''))
        self.assertEqual(set(expected_tracks), tracks)

    def test_unicode_cache(self):
        tracks = parse_mpd_tag_cache(data_folder('utf8_tag_cache'),
             data_folder(''))

        uri = path_to_uri(data_folder('song1.mp3'))
        artists = [Artist(name=u'æøå')]
        album = Album(name=u'æøå', artists=artists)
        track = Track(uri=uri, name=u'æøå', artists=artists,
            album=album, length=4000)

        self.assertEqual(track, list(tracks)[0])

    def test_misencoded_cache(self):
        # FIXME not sure if this can happen
        raise SkipTest

    def test_cache_with_blank_track_info(self):
        tracks = parse_mpd_tag_cache(data_folder('blank_tag_cache'),
            data_folder(''))
        uri = path_to_uri(data_folder('song1.mp3'))
        self.assertEqual(set([Track(uri=uri, length=4000)]), tracks)
