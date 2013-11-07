# encoding: utf-8

from __future__ import unicode_literals

import os
import tempfile
import unittest

from mopidy.backends.local.translator import parse_m3u, parse_mpd_tag_cache
from mopidy.models import Track, Artist, Album
from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir

data_dir = path_to_data_dir('')
song1_path = path_to_data_dir('song1.mp3')
song2_path = path_to_data_dir('song2.mp3')
encoded_path = path_to_data_dir('æøå.mp3')
song1_uri = path_to_uri(song1_path)
song2_uri = path_to_uri(song2_path)
encoded_uri = path_to_uri(encoded_path)

# FIXME use mock instead of tempfile.NamedTemporaryFile


class M3UToUriTest(unittest.TestCase):
    def test_empty_file(self):
        uris = parse_m3u(path_to_data_dir('empty.m3u'), data_dir)
        self.assertEqual([], uris)

    def test_basic_file(self):
        uris = parse_m3u(path_to_data_dir('one.m3u'), data_dir)
        self.assertEqual([song1_uri], uris)

    def test_file_with_comment(self):
        uris = parse_m3u(path_to_data_dir('comment.m3u'), data_dir)
        self.assertEqual([song1_uri], uris)

    def test_file_is_relative_to_correct_dir(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write('song1.mp3')
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path)
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_multiple_absolute_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_path + '\n')
            tmp.write('# comment \n')
            tmp.write(song2_path)
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri, song2_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_file_with_uri(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(song1_uri)
        try:
            uris = parse_m3u(tmp.name, data_dir)
            self.assertEqual([song1_uri], uris)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_encoding_is_latin1(self):
        uris = parse_m3u(path_to_data_dir('encoding.m3u'), data_dir)
        self.assertEqual([encoded_uri], uris)

    def test_open_missing_file(self):
        uris = parse_m3u(path_to_data_dir('non-existant.m3u'), data_dir)
        self.assertEqual([], uris)


class URItoM3UTest(unittest.TestCase):
    pass


expected_artists = [Artist(name='name')]
expected_albums = [
    Album(name='albumname', artists=expected_artists, num_tracks=2),
    Album(name='albumname', num_tracks=2),
]
expected_tracks = []


def generate_track(path, ident, album_id):
    uri = 'local:track:%s' % path
    track = Track(
        uri=uri, name='trackname', artists=expected_artists,
        album=expected_albums[album_id], track_no=1, date='2006', length=4000,
        last_modified=1272319626)
    expected_tracks.append(track)


generate_track('song1.mp3', 6, 0)
generate_track('song2.mp3', 7, 0)
generate_track('song3.mp3', 8, 1)
generate_track('subdir1/song4.mp3', 2, 0)
generate_track('subdir1/song5.mp3', 3, 0)
generate_track('subdir2/song6.mp3', 4, 1)
generate_track('subdir2/song7.mp3', 5, 1)
generate_track('subdir1/subsubdir/song8.mp3', 0, 0)
generate_track('subdir1/subsubdir/song9.mp3', 1, 1)


class MPDTagCacheToTracksTest(unittest.TestCase):
    def test_emtpy_cache(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('empty_tag_cache'), path_to_data_dir(''))
        self.assertEqual(set(), tracks)

    def test_simple_cache(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('simple_tag_cache'), path_to_data_dir(''))
        track = Track(
            uri='local:track:song1.mp3', name='trackname',
            artists=expected_artists, track_no=1, album=expected_albums[0],
            date='2006', length=4000, last_modified=1272319626)
        self.assertEqual(set([track]), tracks)

    def test_advanced_cache(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('advanced_tag_cache'), path_to_data_dir(''))
        self.assertEqual(set(expected_tracks), tracks)

    def test_unicode_cache(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('utf8_tag_cache'), path_to_data_dir(''))

        artists = [Artist(name='æøå')]
        album = Album(name='æøå', artists=artists)
        track = Track(
            uri='local:track:song1.mp3', name='æøå', artists=artists,
            album=album, length=4000, last_modified=1272319626)

        self.assertEqual(track, list(tracks)[0])

    @unittest.SkipTest
    def test_misencoded_cache(self):
        # FIXME not sure if this can happen
        pass

    def test_cache_with_blank_track_info(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('blank_tag_cache'), path_to_data_dir(''))
        expected = Track(
            uri='local:track:song1.mp3', length=4000, last_modified=1272319626)
        self.assertEqual(set([expected]), tracks)

    def test_musicbrainz_tagcache(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('musicbrainz_tag_cache'), path_to_data_dir(''))
        artist = list(expected_tracks[0].artists)[0].copy(
            musicbrainz_id='7364dea6-ca9a-48e3-be01-b44ad0d19897')
        albumartist = list(expected_tracks[0].artists)[0].copy(
            name='albumartistname',
            musicbrainz_id='7364dea6-ca9a-48e3-be01-b44ad0d19897')
        album = expected_tracks[0].album.copy(
            artists=[albumartist],
            musicbrainz_id='cb5f1603-d314-4c9c-91e5-e295cfb125d2')
        track = expected_tracks[0].copy(
            artists=[artist], album=album,
            musicbrainz_id='90488461-8c1f-4a4e-826b-4c6dc70801f0')

        self.assertEqual(track, list(tracks)[0])

    def test_albumartist_tag_cache(self):
        tracks = parse_mpd_tag_cache(
            path_to_data_dir('albumartist_tag_cache'), path_to_data_dir(''))
        artist = Artist(name='albumartistname')
        album = expected_albums[0].copy(artists=[artist])
        track = Track(
            uri='local:track:song1.mp3', name='trackname',
            artists=expected_artists, track_no=1, album=album, date='2006',
            length=4000, last_modified=1272319626)
        self.assertEqual(track, list(tracks)[0])
