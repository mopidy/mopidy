from __future__ import unicode_literals

from mopidy.models import Track

from tests.frontends.mpd import protocol


class CurrentPlaylistHandlerTest(protocol.BaseTestCase):
    def test_add(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.dummy_library = [
            Track(), Track(), needle, Track()]
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('add "dummy://foo"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 6)
        self.assertEqual(self.core.tracklist.tracks.get()[5], needle)
        self.assertEqualResponse('OK')

    def test_add_with_uri_not_found_in_library_should_ack(self):
        self.sendRequest('add "dummy://foo"')
        self.assertEqualResponse(
            'ACK [50@0] {add} directory or file not found')

    def test_add_with_empty_uri_should_add_all_known_tracks_and_ok(self):
        self.sendRequest('add ""')
        # TODO check that we add all tracks (we currently don't)
        self.assertInResponse('OK')

    def test_addid_without_songpos(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.dummy_library = [
            Track(), Track(), needle, Track()]
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('addid "dummy://foo"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 6)
        self.assertEqual(self.core.tracklist.tracks.get()[5], needle)
        self.assertInResponse(
            'Id: %d' % self.core.tracklist.tl_tracks.get()[5].tlid)
        self.assertInResponse('OK')

    def test_addid_with_empty_uri_acks(self):
        self.sendRequest('addid ""')
        self.assertEqualResponse('ACK [50@0] {addid} No such song')

    def test_addid_with_songpos(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.dummy_library = [
            Track(), Track(), needle, Track()]
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('addid "dummy://foo" "3"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 6)
        self.assertEqual(self.core.tracklist.tracks.get()[3], needle)
        self.assertInResponse(
            'Id: %d' % self.core.tracklist.tl_tracks.get()[3].tlid)
        self.assertInResponse('OK')

    def test_addid_with_songpos_out_of_bounds_should_ack(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.dummy_library = [
            Track(), Track(), needle, Track()]
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('addid "dummy://foo" "6"')
        self.assertEqualResponse('ACK [2@0] {addid} Bad song index')

    def test_addid_with_uri_not_found_in_library_should_ack(self):
        self.sendRequest('addid "dummy://foo"')
        self.assertEqualResponse('ACK [50@0] {addid} No such song')

    def test_clear(self):
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('clear')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 0)
        self.assertEqual(self.core.playback.current_track.get(), None)
        self.assertInResponse('OK')

    def test_delete_songpos(self):
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest(
            'delete "%d"' % self.core.tracklist.tl_tracks.get()[2].tlid)
        self.assertEqual(len(self.core.tracklist.tracks.get()), 4)
        self.assertInResponse('OK')

    def test_delete_songpos_out_of_bounds(self):
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('delete "5"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)
        self.assertEqualResponse('ACK [2@0] {delete} Bad song index')

    def test_delete_open_range(self):
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('delete "1:"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 1)
        self.assertInResponse('OK')

    def test_delete_closed_range(self):
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('delete "1:3"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 3)
        self.assertInResponse('OK')

    def test_delete_range_out_of_bounds(self):
        self.core.tracklist.add(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)

        self.sendRequest('delete "5:7"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 5)
        self.assertEqualResponse('ACK [2@0] {delete} Bad song index')

    def test_deleteid(self):
        self.core.tracklist.add([Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)

        self.sendRequest('deleteid "1"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 1)
        self.assertInResponse('OK')

    def test_deleteid_does_not_exist(self):
        self.core.tracklist.add([Track(), Track()])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)

        self.sendRequest('deleteid "12345"')
        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.assertEqualResponse('ACK [50@0] {deleteid} No such song')

    def test_move_songpos(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('move "1" "0"')
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'b')
        self.assertEqual(tracks[1].name, 'a')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse('OK')

    def test_move_open_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('move "2:" "0"')
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'c')
        self.assertEqual(tracks[1].name, 'd')
        self.assertEqual(tracks[2].name, 'e')
        self.assertEqual(tracks[3].name, 'f')
        self.assertEqual(tracks[4].name, 'a')
        self.assertEqual(tracks[5].name, 'b')
        self.assertInResponse('OK')

    def test_move_closed_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('move "1:3" "0"')
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'b')
        self.assertEqual(tracks[1].name, 'c')
        self.assertEqual(tracks[2].name, 'a')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse('OK')

    def test_moveid(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('moveid "4" "2"')
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'b')
        self.assertEqual(tracks[2].name, 'e')
        self.assertEqual(tracks[3].name, 'c')
        self.assertEqual(tracks[4].name, 'd')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse('OK')

    def test_moveid_with_tlid_not_found_in_tracklist_should_ack(self):
        self.sendRequest('moveid "9" "0"')
        self.assertEqualResponse(
            'ACK [50@0] {moveid} No such song')

    def test_playlist_returns_same_as_playlistinfo(self):
        playlist_response = self.sendRequest('playlist')
        playlistinfo_response = self.sendRequest('playlistinfo')
        self.assertEqual(playlist_response, playlistinfo_response)

    def test_playlistfind(self):
        self.sendRequest('playlistfind "tag" "needle"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_playlistfind_by_filename_not_in_tracklist(self):
        self.sendRequest('playlistfind "filename" "file:///dev/null"')
        self.assertEqualResponse('OK')

    def test_playlistfind_by_filename_without_quotes(self):
        self.sendRequest('playlistfind filename "file:///dev/null"')
        self.assertEqualResponse('OK')

    def test_playlistfind_by_filename_in_tracklist(self):
        self.core.tracklist.add([Track(uri='file:///exists')])

        self.sendRequest('playlistfind filename "file:///exists"')
        self.assertInResponse('file: file:///exists')
        self.assertInResponse('Id: 0')
        self.assertInResponse('Pos: 0')
        self.assertInResponse('OK')

    def test_playlistid_without_songid(self):
        self.core.tracklist.add([Track(name='a'), Track(name='b')])

        self.sendRequest('playlistid')
        self.assertInResponse('Title: a')
        self.assertInResponse('Title: b')
        self.assertInResponse('OK')

    def test_playlistid_with_songid(self):
        self.core.tracklist.add([Track(name='a'), Track(name='b')])

        self.sendRequest('playlistid "1"')
        self.assertNotInResponse('Title: a')
        self.assertNotInResponse('Id: 0')
        self.assertInResponse('Title: b')
        self.assertInResponse('Id: 1')
        self.assertInResponse('OK')

    def test_playlistid_with_not_existing_songid_fails(self):
        self.core.tracklist.add([Track(name='a'), Track(name='b')])

        self.sendRequest('playlistid "25"')
        self.assertEqualResponse('ACK [50@0] {playlistid} No such song')

    def test_playlistinfo_without_songpos_or_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('playlistinfo')
        self.assertInResponse('Title: a')
        self.assertInResponse('Pos: 0')
        self.assertInResponse('Title: b')
        self.assertInResponse('Pos: 1')
        self.assertInResponse('Title: c')
        self.assertInResponse('Pos: 2')
        self.assertInResponse('Title: d')
        self.assertInResponse('Pos: 3')
        self.assertInResponse('Title: e')
        self.assertInResponse('Pos: 4')
        self.assertInResponse('Title: f')
        self.assertInResponse('Pos: 5')
        self.assertInResponse('OK')

    def test_playlistinfo_with_songpos(self):
        # Make the track's CPID not match the playlist position
        self.core.tracklist.tlid = 17
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('playlistinfo "4"')
        self.assertNotInResponse('Title: a')
        self.assertNotInResponse('Pos: 0')
        self.assertNotInResponse('Title: b')
        self.assertNotInResponse('Pos: 1')
        self.assertNotInResponse('Title: c')
        self.assertNotInResponse('Pos: 2')
        self.assertNotInResponse('Title: d')
        self.assertNotInResponse('Pos: 3')
        self.assertInResponse('Title: e')
        self.assertInResponse('Pos: 4')
        self.assertNotInResponse('Title: f')
        self.assertNotInResponse('Pos: 5')
        self.assertInResponse('OK')

    def test_playlistinfo_with_negative_songpos_same_as_playlistinfo(self):
        response1 = self.sendRequest('playlistinfo "-1"')
        response2 = self.sendRequest('playlistinfo')
        self.assertEqual(response1, response2)

    def test_playlistinfo_with_open_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('playlistinfo "2:"')
        self.assertNotInResponse('Title: a')
        self.assertNotInResponse('Pos: 0')
        self.assertNotInResponse('Title: b')
        self.assertNotInResponse('Pos: 1')
        self.assertInResponse('Title: c')
        self.assertInResponse('Pos: 2')
        self.assertInResponse('Title: d')
        self.assertInResponse('Pos: 3')
        self.assertInResponse('Title: e')
        self.assertInResponse('Pos: 4')
        self.assertInResponse('Title: f')
        self.assertInResponse('Pos: 5')
        self.assertInResponse('OK')

    def test_playlistinfo_with_closed_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('playlistinfo "2:4"')
        self.assertNotInResponse('Title: a')
        self.assertNotInResponse('Title: b')
        self.assertInResponse('Title: c')
        self.assertInResponse('Title: d')
        self.assertNotInResponse('Title: e')
        self.assertNotInResponse('Title: f')
        self.assertInResponse('OK')

    def test_playlistinfo_with_too_high_start_of_range_returns_arg_error(self):
        self.sendRequest('playlistinfo "10:20"')
        self.assertEqualResponse('ACK [2@0] {playlistinfo} Bad song index')

    def test_playlistinfo_with_too_high_end_of_range_returns_ok(self):
        self.sendRequest('playlistinfo "0:20"')
        self.assertInResponse('OK')

    def test_playlistsearch(self):
        self.sendRequest('playlistsearch "any" "needle"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_playlistsearch_without_quotes(self):
        self.sendRequest('playlistsearch any "needle"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_plchanges_with_lower_version_returns_changes(self):
        self.core.tracklist.add(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.sendRequest('plchanges "0"')
        self.assertInResponse('Title: a')
        self.assertInResponse('Title: b')
        self.assertInResponse('Title: c')
        self.assertInResponse('OK')

    def test_plchanges_with_equal_version_returns_nothing(self):
        self.core.tracklist.add(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.assertEqual(self.core.tracklist.version.get(), 1)
        self.sendRequest('plchanges "1"')
        self.assertNotInResponse('Title: a')
        self.assertNotInResponse('Title: b')
        self.assertNotInResponse('Title: c')
        self.assertInResponse('OK')

    def test_plchanges_with_greater_version_returns_nothing(self):
        self.core.tracklist.add(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.assertEqual(self.core.tracklist.version.get(), 1)
        self.sendRequest('plchanges "2"')
        self.assertNotInResponse('Title: a')
        self.assertNotInResponse('Title: b')
        self.assertNotInResponse('Title: c')
        self.assertInResponse('OK')

    def test_plchanges_with_minus_one_returns_entire_playlist(self):
        self.core.tracklist.add(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.sendRequest('plchanges "-1"')
        self.assertInResponse('Title: a')
        self.assertInResponse('Title: b')
        self.assertInResponse('Title: c')
        self.assertInResponse('OK')

    def test_plchanges_without_quotes_works(self):
        self.core.tracklist.add(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.sendRequest('plchanges 0')
        self.assertInResponse('Title: a')
        self.assertInResponse('Title: b')
        self.assertInResponse('Title: c')
        self.assertInResponse('OK')

    def test_plchangesposid(self):
        self.core.tracklist.add([Track(), Track(), Track()])

        self.sendRequest('plchangesposid "0"')
        tl_tracks = self.core.tracklist.tl_tracks.get()
        self.assertInResponse('cpos: 0')
        self.assertInResponse('Id: %d' % tl_tracks[0].tlid)
        self.assertInResponse('cpos: 2')
        self.assertInResponse('Id: %d' % tl_tracks[1].tlid)
        self.assertInResponse('cpos: 2')
        self.assertInResponse('Id: %d' % tl_tracks[2].tlid)
        self.assertInResponse('OK')

    def test_shuffle_without_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.core.tracklist.version.get()

        self.sendRequest('shuffle')
        self.assertLess(version, self.core.tracklist.version.get())
        self.assertInResponse('OK')

    def test_shuffle_with_open_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.core.tracklist.version.get()

        self.sendRequest('shuffle "4:"')
        self.assertLess(version, self.core.tracklist.version.get())
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'b')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertInResponse('OK')

    def test_shuffle_with_closed_range(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.core.tracklist.version.get()

        self.sendRequest('shuffle "1:3"')
        self.assertLess(version, self.core.tracklist.version.get())
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse('OK')

    def test_swap(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('swap "1" "4"')
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'e')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'b')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse('OK')

    def test_swapid(self):
        self.core.tracklist.add([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest('swapid "1" "4"')
        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'e')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'b')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse('OK')

    def test_swapid_with_first_id_unknown_should_ack(self):
        self.core.tracklist.add([Track()])
        self.sendRequest('swapid "0" "4"')
        self.assertEqualResponse(
            'ACK [50@0] {swapid} No such song')

    def test_swapid_with_second_id_unknown_should_ack(self):
        self.core.tracklist.add([Track()])
        self.sendRequest('swapid "4" "0"')
        self.assertEqualResponse(
            'ACK [50@0] {swapid} No such song')
