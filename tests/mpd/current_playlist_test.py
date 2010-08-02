import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track
from mopidy.mpd import frontend

class CurrentPlaylistHandlerTest(unittest.TestCase):
    def setUp(self):
        self.m = DummyMixer()
        self.b = DummyBackend(mixer=self.m)
        self.h = frontend.MpdFrontend(backend=self.b)

    def test_add(self):
        needle = Track(uri='dummy://foo')
        self.b.library._library = [Track(), Track(), needle, Track()]
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'add "dummy://foo"')
        self.assertEqual(len(self.b.current_playlist.tracks), 6)
        self.assertEqual(self.b.current_playlist.tracks[5], needle)
        self.assertEqual(len(result), 1)
        self.assert_(u'OK' in result)

    def test_add_with_uri_not_found_in_library_should_ack(self):
        result = self.h.handle_request(u'add "dummy://foo"')
        self.assertEqual(result[0],
            u'ACK [50@0] {add} directory or file not found')

    def test_addid_without_songpos(self):
        needle = Track(uri='dummy://foo')
        self.b.library._library = [Track(), Track(), needle, Track()]
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'addid "dummy://foo"')
        self.assertEqual(len(self.b.current_playlist.tracks), 6)
        self.assertEqual(self.b.current_playlist.tracks[5], needle)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks[5][0]
            in result)
        self.assert_(u'OK' in result)

    def test_addid_with_songpos(self):
        needle = Track(uri='dummy://foo')
        self.b.library._library = [Track(), Track(), needle, Track()]
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'addid "dummy://foo" "3"')
        self.assertEqual(len(self.b.current_playlist.tracks), 6)
        self.assertEqual(self.b.current_playlist.tracks[3], needle)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks[3][0]
            in result)
        self.assert_(u'OK' in result)

    def test_addid_with_songpos_out_of_bounds_should_ack(self):
        needle = Track(uri='dummy://foo', id=137)
        self.b.library._library = [Track(), Track(), needle, Track()]
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'addid "dummy://foo" "6"')
        self.assertEqual(result[0], u'ACK [2@0] {addid} Bad song index')

    def test_addid_with_uri_not_found_in_library_should_ack(self):
        result = self.h.handle_request(u'addid "dummy://foo"')
        self.assertEqual(result[0], u'ACK [50@0] {addid} No such song')

    def test_clear(self):
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'clear')
        self.assertEqual(len(self.b.current_playlist.tracks), 0)
        self.assertEqual(self.b.playback.current_track, None)
        self.assert_(u'OK' in result)

    def test_delete_songpos(self):
        self.b.current_playlist.load(
            [Track(id=1), Track(id=2), Track(id=3), Track(id=4), Track(id=5)])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'delete "2"')
        self.assertEqual(len(self.b.current_playlist.tracks), 4)
        self.assert_(u'OK' in result)

    def test_delete_songpos_out_of_bounds(self):
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'delete "5"')
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        self.assertEqual(result[0], u'ACK [2@0] {delete} Bad song index')

    def test_delete_open_range(self):
        self.b.current_playlist.load(
            [Track(id=1), Track(id=2), Track(id=3), Track(id=4), Track(id=5)])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'delete "1:"')
        self.assertEqual(len(self.b.current_playlist.tracks), 1)
        self.assert_(u'OK' in result)

    def test_delete_closed_range(self):
        self.b.current_playlist.load(
            [Track(id=1), Track(id=2), Track(id=3), Track(id=4), Track(id=5)])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'delete "1:3"')
        self.assertEqual(len(self.b.current_playlist.tracks), 3)
        self.assert_(u'OK' in result)

    def test_delete_range_out_of_bounds(self):
        self.b.current_playlist.load(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        result = self.h.handle_request(u'delete "5:7"')
        self.assertEqual(len(self.b.current_playlist.tracks), 5)
        self.assertEqual(result[0], u'ACK [2@0] {delete} Bad song index')

    def test_deleteid(self):
        self.b.current_playlist.load([Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 2)
        result = self.h.handle_request(u'deleteid "2"')
        self.assertEqual(len(self.b.current_playlist.tracks), 1)
        self.assert_(u'OK' in result)

    def test_deleteid_does_not_exist(self):
        self.b.current_playlist.load([Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks), 2)
        result = self.h.handle_request(u'deleteid "12345"')
        self.assertEqual(len(self.b.current_playlist.tracks), 2)
        self.assertEqual(result[0], u'ACK [50@0] {deleteid} No such song')

    def test_move_songpos(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'move "1" "0"')
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'b')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_move_open_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'move "2:" "0"')
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'f')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'b')
        self.assert_(u'OK' in result)

    def test_move_closed_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'move "1:3" "0"')
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'b')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_moveid(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'moveid "5" "2"')
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'b')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_playlist_returns_same_as_playlistinfo(self):
        playlist_result = self.h.handle_request(u'playlist')
        playlistinfo_result = self.h.handle_request(u'playlistinfo')
        self.assertEqual(playlist_result, playlistinfo_result)

    def test_playlistfind(self):
        result = self.h.handle_request(u'playlistfind "tag" "needle"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_playlistfind_by_filename(self):
        result = self.h.handle_request(
            u'playlistfind "filename" "file:///dev/null"')
        self.assert_(u'OK' in result)

    def test_playlistfind_by_filename_without_quotes(self):
        result = self.h.handle_request(
            u'playlistfind filename "file:///dev/null"')
        self.assert_(u'OK' in result)

    def test_playlistfind_by_filename_in_current_playlist(self):
        self.b.current_playlist.load([
            Track(uri='file:///exists')])
        result = self.h.handle_request(
            u'playlistfind filename "file:///exists"')
        self.assert_(u'file: file:///exists' in result)
        self.assert_(u'OK' in result)

    def test_playlistid_without_songid(self):
        self.b.current_playlist.load([Track(name='a'), Track(name='b')])
        result = self.h.handle_request(u'playlistid')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'OK' in result)

    def test_playlistid_with_songid(self):
        self.b.current_playlist.load([Track(name='a'), Track(name='b')])
        result = self.h.handle_request(u'playlistid "2"')
        self.assert_(u'Title: a' not in result)
        self.assert_(u'Id: 1' not in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Id: 2' in result)
        self.assert_(u'OK' in result)

    def test_playlistid_with_not_existing_songid_fails(self):
        self.b.current_playlist.load([Track(name='a'), Track(name='b')])
        result = self.h.handle_request(u'playlistid "25"')
        self.assertEqual(result[0], u'ACK [50@0] {playlistid} No such song')

    def test_playlistinfo_without_songpos_or_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'playlistinfo')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'Title: d' in result)
        self.assert_(u'Title: e' in result)
        self.assert_(u'Title: f' in result)
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_songpos(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'playlistinfo "4"')
        self.assert_(u'Title: a' not in result)
        self.assert_(u'Title: b' not in result)
        self.assert_(u'Title: c' not in result)
        self.assert_(u'Title: d' not in result)
        self.assert_(u'Title: e' in result)
        self.assert_(u'Title: f' not in result)
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_negative_songpos_same_as_playlistinfo(self):
        result1 = self.h.handle_request(u'playlistinfo "-1"')
        result2 = self.h.handle_request(u'playlistinfo')
        self.assertEqual(result1, result2)

    def test_playlistinfo_with_open_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'playlistinfo "2:"')
        self.assert_(u'Title: a' not in result)
        self.assert_(u'Title: b' not in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'Title: d' in result)
        self.assert_(u'Title: e' in result)
        self.assert_(u'Title: f' in result)
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_closed_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'playlistinfo "2:4"')
        self.assert_(u'Title: a' not in result)
        self.assert_(u'Title: b' not in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'Title: d' in result)
        self.assert_(u'Title: e' not in result)
        self.assert_(u'Title: f' not in result)
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_too_high_start_of_range_returns_arg_error(self):
        result = self.h.handle_request(u'playlistinfo "10:20"')
        self.assert_(u'ACK [2@0] {playlistinfo} Bad song index' in result)

    def test_playlistinfo_with_too_high_end_of_range_returns_ok(self):
        result = self.h.handle_request(u'playlistinfo "0:20"')
        self.assert_(u'OK' in result)

    def test_playlistsearch(self):
        result = self.h.handle_request(u'playlistsearch "tag" "needle"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_plchanges(self):
        self.b.current_playlist.load(
            [Track(name='a'), Track(name='b'), Track(name='c')])
        result = self.h.handle_request(u'plchanges "0"')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'OK' in result)

    def test_plchangesposid(self):
        self.b.current_playlist.load([Track(), Track(), Track()])
        result = self.h.handle_request(u'plchangesposid "0"')
        self.assert_(u'cpos: 0' in result)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks[0][0]
            in result)
        self.assert_(u'cpos: 2' in result)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks[1][0]
            in result)
        self.assert_(u'cpos: 2' in result)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks[2][0]
            in result)
        self.assert_(u'OK' in result)

    def test_shuffle_without_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.b.current_playlist.version
        result = self.h.handle_request(u'shuffle')
        self.assert_(version < self.b.current_playlist.version)
        self.assert_(u'OK' in result)

    def test_shuffle_with_open_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.b.current_playlist.version
        result = self.h.handle_request(u'shuffle "4:"')
        self.assert_(version < self.b.current_playlist.version)
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'b')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'd')
        self.assert_(u'OK' in result)

    def test_shuffle_with_closed_range(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.b.current_playlist.version
        result = self.h.handle_request(u'shuffle "1:3"')
        self.assert_(version < self.b.current_playlist.version)
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_swap(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'swap "1" "4"')
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'b')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_swapid(self):
        self.b.current_playlist.load([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'swapid "2" "5"')
        self.assertEqual(self.b.current_playlist.tracks[0].name, 'a')
        self.assertEqual(self.b.current_playlist.tracks[1].name, 'e')
        self.assertEqual(self.b.current_playlist.tracks[2].name, 'c')
        self.assertEqual(self.b.current_playlist.tracks[3].name, 'd')
        self.assertEqual(self.b.current_playlist.tracks[4].name, 'b')
        self.assertEqual(self.b.current_playlist.tracks[5].name, 'f')
        self.assert_(u'OK' in result)
