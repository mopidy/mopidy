import datetime as dt
import unittest

from mopidy import settings
from mopidy.frontends.mpd import translator, protocol
from mopidy.models import Album, Artist, Playlist, Track

from tests import data_folder, SkipTest

class TrackMpdFormatTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/dir/subdir'

    def tearDown(self):
        settings.runtime.clear()

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
        result = translator.track_to_mpd_format(Track(), cpid=1)
        self.assert_(('Id', 1) not in result)

    def test_track_to_mpd_format_with_position_and_cpid(self):
        result = translator.track_to_mpd_format(Track(), position=1, cpid=2)
        self.assert_(('Pos', 1) in result)
        self.assert_(('Id', 2) in result)

    def test_track_to_mpd_format_with_key(self):
        track = Track(uri='file:///dir/subdir/file.mp3')
        result = translator.track_to_mpd_format(track, key=True)
        self.assert_(('key', 'file.mp3') in result)

    def test_track_to_mpd_format_with_mtime(self):
        uri = translator.path_to_uri(data_folder('blank.mp3'))
        result = translator.track_to_mpd_format(Track(uri=uri), mtime=True)
        print result
        self.assert_(('mtime', 1288125516) in result)

    def test_track_to_mpd_format_track_uses_uri_to_mpd_relative_path(self):
        track = Track(uri='file:///dir/subdir/song.mp3')
        path = dict(translator.track_to_mpd_format(track))['file']
        correct_path = translator.uri_to_mpd_relative_path(track.uri)
        self.assertEqual(path, correct_path)

    def test_track_to_mpd_format_for_nonempty_track(self):
        track = Track(
            uri=u'a uri',
            artists=[Artist(name=u'an artist')],
            name=u'a name',
            album=Album(name=u'an album', num_tracks=13),
            track_no=7,
            date=dt.date(1977, 1, 1),
            length=137000,
        )
        result = translator.track_to_mpd_format(track, position=9, cpid=122)
        self.assert_(('file', 'a uri') in result)
        self.assert_(('Time', 137) in result)
        self.assert_(('Artist', 'an artist') in result)
        self.assert_(('Title', 'a name') in result)
        self.assert_(('Album', 'an album') in result)
        self.assert_(('Track', '7/13') in result)
        self.assert_(('Date', dt.date(1977, 1, 1)) in result)
        self.assert_(('Pos', 9) in result)
        self.assert_(('Id', 122) in result)
        self.assertEqual(len(result), 9)

    def test_track_artists_to_mpd_format(self):
        track = Track(artists=[Artist(name=u'ABBA'), Artist(name=u'Beatles')])
        translated = translator.track_artists_to_mpd_format(track)
        self.assertEqual(translated, u'ABBA, Beatles')


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


class UriToMpdRelativePathTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/dir/subdir'

    def tearDown(self):
        settings.runtime.clear()

    def test_none_file_returns_empty_string(self):
        uri = 'file:///dir/subdir/music/album/song.mp3'
        result = translator.uri_to_mpd_relative_path(None)
        self.assertEqual('', result)

    def test_file_gets_stripped(self):
        uri = 'file:///dir/subdir/music/album/song.mp3'
        result = translator.uri_to_mpd_relative_path(uri)
        self.assertEqual('/music/album/song.mp3', result)


class TracksToTagCacheFormatTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/dir/subdir'

    def tearDown(self):
        settings.runtime.clear()

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
        self.assertEqual('begin', result[0][0])
        directory = result[0][1]
        for i, row in enumerate(result):
            if row == ('end', directory):
                return result[1:i], result[i+1:]
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
        formated = translator.track_to_mpd_format(track, key=True)
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(song_list, formated)
        self.assertEqual(len(result), 0)

    def test_tag_cache_suports_directories(self):
        track = Track(uri='file:///dir/subdir/folder/song.mp3')
        formated = translator.track_to_mpd_format(track, key=True)
        result = translator.tracks_to_tag_cache_format([track])

        result = self.consume_headers(result)
        folder, result = self.consume_directory(result)
        song_list, result = self.consume_song_list(result)
        self.assertEqual(len(song_list), 0)
        self.assertEqual(len(result), 0)

        song_list, result = self.consume_song_list(folder)
        self.assertEqual(len(result), 0)
        self.assertEqual(song_list, formated)

    def test_tag_cache_suports_sub_directories(self):
        track = Track(uri='file:///dir/subdir/folder/sub/song.mp3')
        formated = translator.track_to_mpd_format(track, key=True)
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
        formated.extend(translator.track_to_mpd_format(tracks[0], key=True))
        formated.extend(translator.track_to_mpd_format(tracks[1], key=True))

        result = translator.tracks_to_tag_cache_format(tracks)

        result = self.consume_headers(result)
        song_list, result = self.consume_song_list(result)

        self.assertEqual(song_list, formated)
        self.assertEqual(len(result), 0)


class TracksToDirectoryTreeTest(unittest.TestCase):
    def setUp(self):
        settings.LOCAL_MUSIC_FOLDER = '/'

    def tearDown(self):
        settings.runtime.clear()

    def test_no_tracks_gives_emtpy_tree(self):
        tree = translator.tracks_to_directory_tree([])
        self.assertEqual(tree, ({}, []))

    def test_top_level_files(self):
        tracks = [
            Track(uri='file:///file1.mp3'),
            Track(uri='file:///file2.mp3'),
            Track(uri='file:///file3.mp3'),
        ]
        tree = translator.tracks_to_directory_tree(tracks)
        self.assertEqual(tree, ({}, tracks))

    def test_single_file_in_subdir(self):
        tracks = [Track(uri='file:///dir/file1.mp3')]
        tree = translator.tracks_to_directory_tree(tracks)
        expected = ({'dir': ({}, tracks)}, [])
        self.assertEqual(tree, expected)

    def test_single_file_in_sub_subdir(self):
        tracks = [Track(uri='file:///dir1/dir2/file1.mp3')]
        tree = translator.tracks_to_directory_tree(tracks)
        expected = ({'dir1': ({'dir2': ({}, tracks)}, [])}, [])
        self.assertEqual(tree, expected)

    def test_complex_file_structure(self):
        tracks = [
            Track(uri='file:///file1.mp3'),
            Track(uri='file:///dir1/file2.mp3'),
            Track(uri='file:///dir1/file3.mp3'),
            Track(uri='file:///dir2/file4.mp3'),
            Track(uri='file:///dir2/sub/file5.mp3'),
        ]
        tree = translator.tracks_to_directory_tree(tracks)
        expected = (
            {
                'dir1': ({}, [tracks[1], tracks[2]]),
                'dir2': (
                    {
                        'sub': ({}, [tracks[4]])
                    },
                    [tracks[3]]
                ),
            },
            [tracks[0]]
        )
        self.assertEqual(tree, expected)
