import datetime
import os

from mopidy import settings
from mopidy.utils.path import mtime, uri_to_path
from mopidy.frontends.mpd import translator, protocol
from mopidy.models import Album, Artist, CpTrack, Playlist, Track

from tests import unittest


class TrackMpdFormatTest(unittest.TestCase):
    track = Track(
        uri=u'a uri',
        artists=[Artist(name=u'an artist')],
        name=u'a name',
        album=Album(name=u'an album', num_tracks=13,
            artists=[Artist(name=u'an other artist')]),
        track_no=7,
        date=datetime.date(1977, 1, 1),
        length=137000,
    )

    def setUp(self):
        settings.LOCAL_MUSIC_PATH = '/dir/subdir'
        mtime.set_fake_time(1234567)

    def tearDown(self):
        settings.runtime.clear()
        mtime.undo_fake()

    def test_track_to_mpd_format_for_empty_track(self):
        result = translator.track_to_mpd_format(Track())
        self.assert_(('file', '') in result)
        self.assert_(('Time', 0) in result)
        self.assert_(('Artist', '') in result)
        self.assert_(('Title', '') in result)
        self.assert_(('Album', '') in result)
        self.assert_(('Track', 0) in result)
        self.assert_(('Date', '') in result)
        self.assertEqual(len(result), 7)

    def test_track_to_mpd_format_with_position(self):
        result = translator.track_to_mpd_format(Track(), position=1)
        self.assert_(('Pos', 1) not in result)

    def test_track_to_mpd_format_with_cpid(self):
        result = translator.track_to_mpd_format(CpTrack(1, Track()))
        self.assert_(('Id', 1) not in result)

    def test_track_to_mpd_format_with_position_and_cpid(self):
        result = translator.track_to_mpd_format(CpTrack(2, Track()), position=1)
        self.assert_(('Pos', 1) in result)
        self.assert_(('Id', 2) in result)

    def test_track_to_mpd_format_for_nonempty_track(self):
        result = translator.track_to_mpd_format(
            CpTrack(122, self.track), position=9)
        self.assert_(('file', 'a uri') in result)
        self.assert_(('Time', 137) in result)
        self.assert_(('Artist', 'an artist') in result)
        self.assert_(('Title', 'a name') in result)
        self.assert_(('Album', 'an album') in result)
        self.assert_(('AlbumArtist', 'an other artist') in result)
        self.assert_(('Track', '7/13') in result)
        self.assert_(('Date', datetime.date(1977, 1, 1)) in result)
        self.assert_(('Pos', 9) in result)
        self.assert_(('Id', 122) in result)
        self.assertEqual(len(result), 10)

    def test_track_to_mpd_format_musicbrainz_trackid(self):
        track = self.track.copy(musicbrainz_id='foo')
        result = translator.track_to_mpd_format(track)
        self.assert_(('MUSICBRAINZ_TRACKID', 'foo') in result)

    def test_track_to_mpd_format_musicbrainz_albumid(self):
        album = self.track.album.copy(musicbrainz_id='foo')
        track = self.track.copy(album=album)
        result = translator.track_to_mpd_format(track)
        self.assert_(('MUSICBRAINZ_ALBUMID', 'foo') in result)

    def test_track_to_mpd_format_musicbrainz_albumid(self):
        artist = list(self.track.artists)[0].copy(musicbrainz_id='foo')
        album = self.track.album.copy(artists=[artist])
        track = self.track.copy(album=album)
        result = translator.track_to_mpd_format(track)
        self.assert_(('MUSICBRAINZ_ALBUMARTISTID', 'foo') in result)

    def test_track_to_mpd_format_musicbrainz_artistid(self):
        artist = list(self.track.artists)[0].copy(musicbrainz_id='foo')
        track = self.track.copy(artists=[artist])
        result = translator.track_to_mpd_format(track)
        self.assert_(('MUSICBRAINZ_ARTISTID', 'foo') in result)

    def test_artists_to_mpd_format(self):
        artists = [Artist(name=u'ABBA'), Artist(name=u'Beatles')]
        translated = translator.artists_to_mpd_format(artists)
        self.assertEqual(translated, u'ABBA, Beatles')

    def test_artists_to_mpd_format_artist_with_no_name(self):
        artists = [Artist(name=None)]
        translated = translator.artists_to_mpd_format(artists)
        self.assertEqual(translated, u'')


class PlaylistMpdFormatTest(unittest.TestCase):
    def test_mpd_format(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist)
        self.assertEqual(len(result), 3)

    def test_mpd_format_with_range(self):
        playlist = Playlist(tracks=[
            Track(track_no=1), Track(track_no=2), Track(track_no=3)])
        result = translator.playlist_to_mpd_format(playlist, 1, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(dict(result[0])['Track'], 2)


class TracksToTagCacheFormatTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_PATH = '/dir/subdir'
        mtime.set_fake_time(1234567)

    def tearDown(self):
        settings.runtime.clear()
        mtime.undo_fake()

    def translate(self, track):
        folder = settings.LOCAL_MUSIC_PATH
        result = dict(translator.track_to_mpd_format(track))
        result['file'] = uri_to_path(result['file'])
        result['file'] = result['file'][len(folder)+1:]
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
                return result[1:i], result[i+1:]
        self.fail("Couldn't find songList end in result")

    def consume_directory(self, result):
        self.assertEqual('directory', result[0][0])
        self.assertEqual(('mtime', mtime('.')), result[1])
        self.assertEqual(('begin', os.path.split(result[0][1])[1]), result[2])
        directory = result[2][1]
        for i, row in enumerate(result):
            if row == ('end', directory):
                return result[3:i], result[i+1:]
        self.fail("Couldn't find end %s in result" % directory)

    def test_empty_tag_cache_has_header(self):
        result = translator.tracks_to_tag_cache_format([])
        result = self.consume_headers(result)

    def test_empty_tag_cache_has_song_list(self):
        result = translator.tracks_to_tag_cache_format([])
        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

    def test_tag_cache_has_header(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        result = translator.tracks_to_tag_cache_format([track])
        result = self.consume_headers(result)

    def test_tag_cache_has_song_list(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        result = translator.tracks_to_tag_cache_format([track])
        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assert_(song_list)
        self.assertEqual(len(result), 0)

    def test_tag_cache_has_formated_track(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(song_list, formated)
        self.assertEqual(len(result), 0)

    def test_tag_cache_has_formated_track_with_key_and_mtime(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(song_list, formated)
        self.assertEqual(len(result), 0)

    def test_tag_cache_suports_directories(self):
        track = Track(uri='file:///dir/subdir/folder/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)
        folder, result = self.consume_directory(result)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

        song_list, result = self.consume_song_list(folder)
        self.assertEqual(len(result), 0)
        self.assertEqual(song_list, formated)

    def test_tag_cache_diretory_header_is_right(self):
        track = Track(uri='file:///dir/subdir/folder/sub/song.mp3')
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)
        folder, result = self.consume_directory(result)

        self.assertEqual(('directory', 'folder/sub'), folder[0])
        self.assertEqual(('mtime', mtime('.')), folder[1])
        self.assertEqual(('begin', 'sub'), folder[2])

    def test_tag_cache_suports_sub_directories(self):
        track = Track(uri='file:///dir/subdir/folder/sub/song.mp3')
        formated = self.translate(track)
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)

        folder, result = self.consume_directory(result)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

        folder, result = self.consume_directory(folder)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(result), 0)
        self.assertEqual(len(song_list), 0)

        song_list, result = self.consume_song_list(folder)
        self.assertEqual(len(result), 0)
        self.assertEqual(song_list, formated)

    def test_tag_cache_supports_multiple_tracks(self):
        tracks = [
            Track(uri='file:///dir/subdir/song1.mp3'),
            Track(uri='file:///dir/subdir/song2.mp3'),
        ]

        formated = []
        formated.extend(self.translate(tracks[0]))
        formated.extend(self.translate(tracks[1]))

        result = translator.tracks_to_tag_cache_format(tracks)

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(song_list, formated)
        self.assertEqual(len(result), 0)

    def test_tag_cache_supports_multiple_tracks_in_dirs(self):
        tracks = [
            Track(uri='file:///dir/subdir/song1.mp3'),
            Track(uri='file:///dir/subdir/folder/song2.mp3'),
        ]

        formated = []
        formated.append(self.translate(tracks[0]))
        formated.append(self.translate(tracks[1]))

        result = translator.tracks_to_tag_cache_format(tracks)

        result = self.consume_headers(result)
        folder, result = self.consume_directory(result)
        song_list, song_result = self.consume_song_list(folder)

        self.assertEqual(song_list, formated[1])
        self.assertEqual(len(song_result), 0)

        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(result), 0)
        self.assertEqual(song_list, formated[0])


class TracksToDirectoryTreeTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_PATH = '/root/'

    def tearDown(self):
        settings.runtime.clear()

    def test_no_tracks_gives_emtpy_tree(self):
        tree = translator.tracks_to_directory_tree([])
        self.assertEqual(tree, ({}, []))

    def test_top_level_files(self):
        tracks = [
            Track(uri='file:///root/file1.mp3'),
            Track(uri='file:///root/file2.mp3'),
            Track(uri='file:///root/file3.mp3'),
        ]
        tree = translator.tracks_to_directory_tree(tracks)
        self.assertEqual(tree, ({}, tracks))

    def test_single_file_in_subdir(self):
        tracks = [Track(uri='file:///root/dir/file1.mp3')]
        tree = translator.tracks_to_directory_tree(tracks)
        expected = ({'dir': ({}, tracks)}, [])
        self.assertEqual(tree, expected)

    def test_single_file_in_sub_subdir(self):
        tracks = [Track(uri='file:///root/dir1/dir2/file1.mp3')]
        tree = translator.tracks_to_directory_tree(tracks)
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
        tree = translator.tracks_to_directory_tree(tracks)
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
