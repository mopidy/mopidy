#encoding: utf-8

import os
import tempfile
import unittest
import urllib

from mopidy.utils import parse_m3u, parse_mpd_tag_cache
from mopidy.models import Track, Artist, Album

from tests import SkipTest, data_folder

song1_path = data_folder('song1.mp3')
song2_path = data_folder('song2.mp3')
encoded_path = data_folder(u'æøå.mp3')
song1_uri = 'file://' + urllib.pathname2url(song1_path)
song2_uri = 'file://' + urllib.pathname2url(song2_path)
encoded_uri = 'file://' + urllib.pathname2url(encoded_path.encode('utf-8'))


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
        with tempfile.NamedTemporaryFile() as file:
            file.write(song1_path)
            file.flush()
            uris = parse_m3u(file.name)
        self.assertEqual([song1_uri], uris)

    def test_file_with_multiple_absolute_files(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(song1_path+'\n')
            file.write('# comment \n')
            file.write(song2_path)
            file.flush()
            uris = parse_m3u(file.name)
        self.assertEqual([song1_uri, song2_uri], uris)

    def test_file_with_uri(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(song1_uri)
            file.flush()
            uris = parse_m3u(file.name)
        self.assertEqual([song1_uri], uris)

    def test_encoding_is_latin1(self):
        uris = parse_m3u(data_folder('encoding.m3u'))
        self.assertEqual([encoded_uri], uris)

expected_artists = [Artist(name='name')]
expected_albums = [Album(name='albumname', artists=expected_artists, num_tracks=2)]
expected_tracks = []

def generate_track(path):
    uri = 'file://' + urllib.pathname2url(data_folder(path))
    track = Track(name='trackname', artists=expected_artists, track_no=1,
        album=expected_albums[0], length=4000, uri=uri)
    expected_tracks.append(track)

generate_track('song1.mp3')
generate_track('song2.mp3')
generate_track('song3.mp3')
generate_track('subdir1/song4.mp3')
generate_track('subdir1/song5.mp3')
generate_track('subdir2/song6.mp3')
generate_track('subdir2/song7.mp3')
generate_track('subdir1/subsubdir/song8.mp3')
generate_track('subdir1/subsubdir/song9.mp3')

class MPDTagCacheToTracksTest(unittest.TestCase):
    def test_emtpy_cache(self):
        tracks, artists, albums = parse_mpd_tag_cache(data_folder('empty_tag_cache'),
            data_folder(''))
        self.assertEqual(set(), tracks)
        self.assertEqual(set(), artists)
        self.assertEqual(set(), albums)

    def test_simple_cache(self):
        tracks, artists, albums = parse_mpd_tag_cache(data_folder('simple_tag_cache'),
            data_folder(''))

        self.assertEqual(expected_tracks[0], list(tracks)[0])
        self.assertEqual(set(expected_artists), artists)
        self.assertEqual(set(expected_albums), albums)

    def test_advanced_cache(self):
        tracks, artists, albums = parse_mpd_tag_cache(data_folder('advanced_tag_cache'),
             data_folder(''))

        self.assertEqual(set(expected_tracks), tracks)
        self.assertEqual(set(expected_artists), artists)
        self.assertEqual(set(expected_albums), albums)

    def test_unicode_cache(self):
        raise SkipTest

    def test_misencoded_cache(self):
        # FIXME not sure if this can happen
        raise SkipTest

    def test_cache_with_blank_track_info(self):
        tracks, artists, albums = parse_mpd_tag_cache(data_folder('blank_tag_cache'),
            data_folder(''))

        uri = 'file://' + urllib.pathname2url(data_folder('song1.mp3'))

        self.assertEqual(set([Track(uri=uri, length=4000)]), tracks)
        self.assertEqual(set(), artists)
        self.assertEqual(set(), albums)

