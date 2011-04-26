import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track

class CurrentPlaylistHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_add(self):
        needle = Track(uri='dummy://foo')
        self.b.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'add "dummy://foo"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], u'OK')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 6)
        self.assertEqual(self.b.current_playlist.tracks.get()[5], needle)

    def test_add_with_uri_not_found_in_library_should_ack(self):
        result = self.h.handle_request(u'add "dummy://foo"')
        self.assertEqual(result[0],
            u'ACK [50@0] {add} directory or file not found')

    def test_add_with_empty_uri_should_add_all_known_tracks_and_ok(self):
        result = self.h.handle_request(u'add ""')
        # TODO check that we add all tracks (we currently don't)
        self.assert_(u'OK' in result)

    def test_addid_without_songpos(self):
        needle = Track(uri='dummy://foo')
        self.b.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'addid "dummy://foo"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 6)
        self.assertEqual(self.b.current_playlist.tracks.get()[5], needle)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks.get()[5][0]
            in result)
        self.assert_(u'OK' in result)

    def test_addid_with_empty_uri_acks(self):
        result = self.h.handle_request(u'addid ""')
        self.assertEqual(result[0], u'ACK [50@0] {addid} No such song')

    def test_addid_with_songpos(self):
        needle = Track(uri='dummy://foo')
        self.b.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'addid "dummy://foo" "3"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 6)
        self.assertEqual(self.b.current_playlist.tracks.get()[3], needle)
        self.assert_(u'Id: %d' % self.b.current_playlist.cp_tracks.get()[3][0]
            in result)
        self.assert_(u'OK' in result)

    def test_addid_with_songpos_out_of_bounds_should_ack(self):
        needle = Track(uri='dummy://foo')
        self.b.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'addid "dummy://foo" "6"')
        self.assertEqual(result[0], u'ACK [2@0] {addid} Bad song index')

    def test_addid_with_uri_not_found_in_library_should_ack(self):
        result = self.h.handle_request(u'addid "dummy://foo"')
        self.assertEqual(result[0], u'ACK [50@0] {addid} No such song')

    def test_clear(self):
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'clear')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 0)
        self.assertEqual(self.b.playback.current_track.get(), None)
        self.assert_(u'OK' in result)

    def test_delete_songpos(self):
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'delete "%d"' %
            self.b.current_playlist.cp_tracks.get()[2][0])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 4)
        self.assert_(u'OK' in result)

    def test_delete_songpos_out_of_bounds(self):
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'delete "5"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        self.assertEqual(result[0], u'ACK [2@0] {delete} Bad song index')

    def test_delete_open_range(self):
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'delete "1:"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 1)
        self.assert_(u'OK' in result)

    def test_delete_closed_range(self):
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'delete "1:3"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 3)
        self.assert_(u'OK' in result)

    def test_delete_range_out_of_bounds(self):
        self.b.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        result = self.h.handle_request(u'delete "5:7"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 5)
        self.assertEqual(result[0], u'ACK [2@0] {delete} Bad song index')

    def test_deleteid(self):
        self.b.current_playlist.append([Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 2)
        result = self.h.handle_request(u'deleteid "1"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 1)
        self.assert_(u'OK' in result)

    def test_deleteid_does_not_exist(self):
        self.b.current_playlist.append([Track(), Track()])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 2)
        result = self.h.handle_request(u'deleteid "12345"')
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 2)
        self.assertEqual(result[0], u'ACK [50@0] {deleteid} No such song')

    def test_move_songpos(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'move "1" "0"')
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'b')
        self.assertEqual(tracks[1].name, 'a')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_move_open_range(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'move "2:" "0"')
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'c')
        self.assertEqual(tracks[1].name, 'd')
        self.assertEqual(tracks[2].name, 'e')
        self.assertEqual(tracks[3].name, 'f')
        self.assertEqual(tracks[4].name, 'a')
        self.assertEqual(tracks[5].name, 'b')
        self.assert_(u'OK' in result)

    def test_move_closed_range(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'move "1:3" "0"')
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'b')
        self.assertEqual(tracks[1].name, 'c')
        self.assertEqual(tracks[2].name, 'a')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_moveid(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'moveid "4" "2"')
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'b')
        self.assertEqual(tracks[2].name, 'e')
        self.assertEqual(tracks[3].name, 'c')
        self.assertEqual(tracks[4].name, 'd')
        self.assertEqual(tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_playlist_returns_same_as_playlistinfo(self):
        playlist_result = self.h.handle_request(u'playlist')
        playlistinfo_result = self.h.handle_request(u'playlistinfo')
        self.assertEqual(playlist_result, playlistinfo_result)

    def test_playlistfind(self):
        result = self.h.handle_request(u'playlistfind "tag" "needle"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_playlistfind_by_filename_not_in_current_playlist(self):
        result = self.h.handle_request(
            u'playlistfind "filename" "file:///dev/null"')
        self.assertEqual(len(result), 1)
        self.assert_(u'OK' in result)

    def test_playlistfind_by_filename_without_quotes(self):
        result = self.h.handle_request(
            u'playlistfind filename "file:///dev/null"')
        self.assertEqual(len(result), 1)
        self.assert_(u'OK' in result)

    def test_playlistfind_by_filename_in_current_playlist(self):
        self.b.current_playlist.append([
            Track(uri='file:///exists')])
        result = self.h.handle_request(
            u'playlistfind filename "file:///exists"')
        self.assert_(u'file: file:///exists' in result)
        self.assert_(u'Id: 0' in result)
        self.assert_(u'Pos: 0' in result)
        self.assert_(u'OK' in result)

    def test_playlistid_without_songid(self):
        self.b.current_playlist.append([Track(name='a'), Track(name='b')])
        result = self.h.handle_request(u'playlistid')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'OK' in result)

    def test_playlistid_with_songid(self):
        self.b.current_playlist.append([Track(name='a'), Track(name='b')])
        result = self.h.handle_request(u'playlistid "1"')
        self.assert_(u'Title: a' not in result)
        self.assert_(u'Id: 0' not in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Id: 1' in result)
        self.assert_(u'OK' in result)

    def test_playlistid_with_not_existing_songid_fails(self):
        self.b.current_playlist.append([Track(name='a'), Track(name='b')])
        result = self.h.handle_request(u'playlistid "25"')
        self.assertEqual(result[0], u'ACK [50@0] {playlistid} No such song')

    def test_playlistinfo_without_songpos_or_range(self):
        self.b.current_playlist.append([
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
        self.b.current_playlist.append([
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
        self.b.current_playlist.append([
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
        self.b.current_playlist.append([
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
        result = self.h.handle_request(u'playlistsearch "any" "needle"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_playlistsearch_without_quotes(self):
        result = self.h.handle_request(u'playlistsearch any "needle"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_plchanges(self):
        self.b.current_playlist.append(
            [Track(name='a'), Track(name='b'), Track(name='c')])
        result = self.h.handle_request(u'plchanges "0"')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'OK' in result)

    def test_plchanges_with_minus_one_returns_entire_playlist(self):
        self.b.current_playlist.append(
            [Track(name='a'), Track(name='b'), Track(name='c')])
        result = self.h.handle_request(u'plchanges "-1"')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'OK' in result)

    def test_plchanges_without_quotes_works(self):
        self.b.current_playlist.append(
            [Track(name='a'), Track(name='b'), Track(name='c')])
        result = self.h.handle_request(u'plchanges 0')
        self.assert_(u'Title: a' in result)
        self.assert_(u'Title: b' in result)
        self.assert_(u'Title: c' in result)
        self.assert_(u'OK' in result)

    def test_plchangesposid(self):
        self.b.current_playlist.append([Track(), Track(), Track()])
        result = self.h.handle_request(u'plchangesposid "0"')
        cp_tracks = self.b.current_playlist.cp_tracks.get()
        self.assert_(u'cpos: 0' in result)
        self.assert_(u'Id: %d' % cp_tracks[0][0]
            in result)
        self.assert_(u'cpos: 2' in result)
        self.assert_(u'Id: %d' % cp_tracks[1][0]
            in result)
        self.assert_(u'cpos: 2' in result)
        self.assert_(u'Id: %d' % cp_tracks[2][0]
            in result)
        self.assert_(u'OK' in result)

    def test_shuffle_without_range(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.b.current_playlist.version.get()
        result = self.h.handle_request(u'shuffle')
        self.assert_(version < self.b.current_playlist.version.get())
        self.assert_(u'OK' in result)

    def test_shuffle_with_open_range(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.b.current_playlist.version.get()
        result = self.h.handle_request(u'shuffle "4:"')
        self.assert_(version < self.b.current_playlist.version.get())
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'b')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assert_(u'OK' in result)

    def test_shuffle_with_closed_range(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.b.current_playlist.version.get()
        result = self.h.handle_request(u'shuffle "1:3"')
        self.assert_(version < self.b.current_playlist.version.get())
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_swap(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'swap "1" "4"')
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'e')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'b')
        self.assertEqual(tracks[5].name, 'f')
        self.assert_(u'OK' in result)

    def test_swapid(self):
        self.b.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        result = self.h.handle_request(u'swapid "1" "4"')
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'e')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'b')
        self.assertEqual(tracks[5].name, 'f')
        self.assert_(u'OK' in result)
