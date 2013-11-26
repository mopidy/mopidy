# encoding: utf-8

from __future__ import unicode_literals

import os
import unittest

from mopidy.utils.path import mtime, uri_to_path
from mopidy.frontends.mpd import translator as mpd, protocol
from mopidy.backends.local.tagcache import translator
from mopidy.models import Album, Artist, Track

from tests import path_to_data_dir


class TracksToTagCacheFormatTest(unittest.TestCase):
    def setUp(self):
        self.media_dir = '/dir/subdir'
        mtime.set_fake_time(1234567)

    def tearDown(self):
        mtime.undo_fake()

    def translate(self, track):
        base_path = self.media_dir.encode('utf-8')
        result = dict(mpd.track_to_mpd_format(track))
        result['file'] = uri_to_path(result['file'])[len(base_path) + 1:]
        result['key'] = os.path.basename(result['file'])
        result['mtime'] = mtime('')
        return translator.order_mpd_track_info(result.items())

    def consume_headers(self, result):
        self.assertEqual(('info_begin',), result[0])
        self.assertEqual(('mpd_version', protocol.VERSION), result[1])
        self.assertEqual(('fs_charset', protocol.ENCODING), result[2])
        self.assertEqual(('info_end',), result[3])
        return result[4:]

    def consume_song_list(self, result):
        self.assertEqual(('songList begin',), result[0])
        for i, row in enumerate(result):
            if row == ('songList end',):
                return result[1:i], result[i + 1:]
        self.fail("Couldn't find songList end in result")

    def consume_directory(self, result):
        self.assertEqual('directory', result[0][0])
        self.assertEqual(('mtime', mtime('.')), result[1])
        self.assertEqual(('begin', os.path.split(result[0][1])[1]), result[2])
        directory = result[2][1]
        for i, row in enumerate(result):
            if row == ('end', directory):
                return result[3:i], result[i + 1:]
        self.fail("Couldn't find end %s in result" % directory)

    def test_empty_tag_cache_has_header(self):
        result = translator.tracks_to_tag_cache_format([], self.media_dir)
        result = self.consume_headers(result)

    def test_empty_tag_cache_has_song_list(self):
        result = translator.tracks_to_tag_cache_format([], self.media_dir)
        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

    def test_tag_cache_has_header(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)
        result = self.consume_headers(result)

    def test_tag_cache_has_song_list(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)
        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assert_(song_list)
        self.assertEqual(len(result), 0)

    def test_tag_cache_has_formated_track(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(formated, song_list)
        self.assertEqual(len(result), 0)

    def test_tag_cache_has_formated_track_with_key_and_mtime(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(formated, song_list)
        self.assertEqual(len(result), 0)

    def test_tag_cache_supports_directories(self):
        track = Track(uri='file:///dir/subdir/folder/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)

        result = self.consume_headers(result)
        dir_data, result = self.consume_directory(result)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

        song_list, result = self.consume_song_list(dir_data)
        self.assertEqual(len(result), 0)
        self.assertEqual(formated, song_list)

    def test_tag_cache_diretory_header_is_right(self):
        track = Track(uri='file:///dir/subdir/folder/sub/song.mp3')
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)

        result = self.consume_headers(result)
        dir_data, result = self.consume_directory(result)

        self.assertEqual(('directory', 'folder/sub'), dir_data[0])
        self.assertEqual(('mtime', mtime('.')), dir_data[1])
        self.assertEqual(('begin', 'sub'), dir_data[2])

    def test_tag_cache_suports_sub_directories(self):
        track = Track(uri='file:///dir/subdir/folder/sub/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track], self.media_dir)

        result = self.consume_headers(result)

        dir_data, result = self.consume_directory(result)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

        dir_data, result = self.consume_directory(dir_data)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(result), 0)
        self.assertEqual(len(song_list), 0)

        song_list, result = self.consume_song_list(dir_data)
        self.assertEqual(len(result), 0)
        self.assertEqual(formated, song_list)

    def test_tag_cache_supports_multiple_tracks(self):
        tracks = [
            Track(uri='file:///dir/subdir/song1.mp3'),
            Track(uri='file:///dir/subdir/song2.mp3'),
        ]

        formated = []
        formated.extend(self.translate(tracks[0]))
        formated.extend(self.translate(tracks[1]))

        result = translator.tracks_to_tag_cache_format(tracks, self.media_dir)

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(formated, song_list)
        self.assertEqual(len(result), 0)

    def test_tag_cache_supports_multiple_tracks_in_dirs(self):
        tracks = [
            Track(uri='file:///dir/subdir/song1.mp3'),
            Track(uri='file:///dir/subdir/folder/song2.mp3'),
        ]

        formated = []
        formated.append(self.translate(tracks[0]))
        formated.append(self.translate(tracks[1]))

        result = translator.tracks_to_tag_cache_format(tracks, self.media_dir)

        result = self.consume_headers(result)
        dir_data, result = self.consume_directory(result)
        song_list, song_result = self.consume_song_list(dir_data)

        self.assertEqual(formated[1], song_list)
        self.assertEqual(len(song_result), 0)

        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(result), 0)
        self.assertEqual(formated[0], song_list)


class TracksToDirectoryTreeTest(unittest.TestCase):
    def setUp(self):
        self.media_dir = '/root'

    def test_no_tracks_gives_emtpy_tree(self):
        tree = translator.tracks_to_directory_tree([], self.media_dir)
        self.assertEqual(tree, ({}, []))

    def test_top_level_files(self):
        tracks = [
            Track(uri='file:///root/file1.mp3'),
            Track(uri='file:///root/file2.mp3'),
            Track(uri='file:///root/file3.mp3'),
        ]
        tree = translator.tracks_to_directory_tree(tracks, self.media_dir)
        self.assertEqual(tree, ({}, tracks))

    def test_single_file_in_subdir(self):
        tracks = [Track(uri='file:///root/dir/file1.mp3')]
        tree = translator.tracks_to_directory_tree(tracks, self.media_dir)
        expected = ({'dir': ({}, tracks)}, [])
        self.assertEqual(tree, expected)

    def test_single_file_in_sub_subdir(self):
        tracks = [Track(uri='file:///root/dir1/dir2/file1.mp3')]
        tree = translator.tracks_to_directory_tree(tracks, self.media_dir)
        expected = ({'dir1': ({'dir1/dir2': ({}, tracks)}, [])}, [])
        self.assertEqual(tree, expected)

    def test_complex_file_structure(self):
        tracks = [
            Track(uri='file:///root/file1.mp3'),
            Track(uri='file:///root/dir1/file2.mp3'),
            Track(uri='file:///root/dir1/file3.mp3'),
            Track(uri='file:///root/dir2/file4.mp3'),
            Track(uri='file:///root/dir2/sub/file5.mp3'),
        ]
        tree = translator.tracks_to_directory_tree(tracks, self.media_dir)
        expected = (
            {
                'dir1': ({}, [tracks[1], tracks[2]]),
                'dir2': (
                    {
                        'dir2/sub': ({}, [tracks[4]])
                    },
                    [tracks[3]]
                ),
            },
            [tracks[0]]
        )
        self.assertEqual(tree, expected)


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
        tracks = translator.parse_mpd_tag_cache(
            path_to_data_dir('empty_tag_cache'), path_to_data_dir(''))
        self.assertEqual(set(), tracks)

    def test_simple_cache(self):
        tracks = translator.parse_mpd_tag_cache(
            path_to_data_dir('simple_tag_cache'), path_to_data_dir(''))
        track = Track(
            uri='local:track:song1.mp3', name='trackname',
            artists=expected_artists, track_no=1, album=expected_albums[0],
            date='2006', length=4000, last_modified=1272319626)
        self.assertEqual(set([track]), tracks)

    def test_advanced_cache(self):
        tracks = translator.parse_mpd_tag_cache(
            path_to_data_dir('advanced_tag_cache'), path_to_data_dir(''))
        self.assertEqual(set(expected_tracks), tracks)

    def test_unicode_cache(self):
        tracks = translator.parse_mpd_tag_cache(
            path_to_data_dir('utf8_tag_cache'), path_to_data_dir(''))

        artists = [Artist(name='æøå')]
        album = Album(name='æøå', artists=artists)
        track = Track(
            uri='local:track:song1.mp3', name='æøå', artists=artists,
            composers=artists, performers=artists, genre='æøå',
            album=album, length=4000, last_modified=1272319626,
            comment='æøå&^`ൂ㔶')

        self.assertEqual(track, list(tracks)[0])

    @unittest.SkipTest
    def test_misencoded_cache(self):
        # FIXME not sure if this can happen
        pass

    def test_cache_with_blank_track_info(self):
        tracks = translator.parse_mpd_tag_cache(
            path_to_data_dir('blank_tag_cache'), path_to_data_dir(''))
        expected = Track(
            uri='local:track:song1.mp3', length=4000, last_modified=1272319626)
        self.assertEqual(set([expected]), tracks)

    def test_musicbrainz_tagcache(self):
        tracks = translator.parse_mpd_tag_cache(
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
        tracks = translator.parse_mpd_tag_cache(
            path_to_data_dir('albumartist_tag_cache'), path_to_data_dir(''))
        artist = Artist(name='albumartistname')
        album = expected_albums[0].copy(artists=[artist])
        track = Track(
            uri='local:track:song1.mp3', name='trackname',
            artists=expected_artists, track_no=1, album=album, date='2006',
            length=4000, last_modified=1272319626)
        self.assertEqual(track, list(tracks)[0])
