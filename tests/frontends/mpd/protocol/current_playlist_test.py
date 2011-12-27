from mopidy.models import Track

from tests.frontends.mpd import protocol


class CurrentPlaylistHandlerTest(protocol.BaseTestCase):
    def test_add(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'add "dummy://foo"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 6)
        self.assertEqual(self.backend.current_playlist.tracks.get()[5], needle)
        self.assertEqualResponse(u'OK')

    def test_add_with_uri_not_found_in_library_should_ack(self):
        self.sendRequest(u'add "dummy://foo"')
        self.assertEqualResponse(
            u'ACK [50@0] {add} directory or file not found')

    def test_add_with_empty_uri_should_add_all_known_tracks_and_ok(self):
        self.sendRequest(u'add ""')
        # TODO check that we add all tracks (we currently don't)
        self.assertInResponse(u'OK')

    def test_addid_without_songpos(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'addid "dummy://foo"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 6)
        self.assertEqual(self.backend.current_playlist.tracks.get()[5], needle)
        self.assertInResponse(u'Id: %d' %
            self.backend.current_playlist.cp_tracks.get()[5][0])
        self.assertInResponse(u'OK')

    def test_addid_with_empty_uri_acks(self):
        self.sendRequest(u'addid ""')
        self.assertEqualResponse(u'ACK [50@0] {addid} No such song')

    def test_addid_with_songpos(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'addid "dummy://foo" "3"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 6)
        self.assertEqual(self.backend.current_playlist.tracks.get()[3], needle)
        self.assertInResponse(u'Id: %d' %
            self.backend.current_playlist.cp_tracks.get()[3][0])
        self.assertInResponse(u'OK')

    def test_addid_with_songpos_out_of_bounds_should_ack(self):
        needle = Track(uri='dummy://foo')
        self.backend.library.provider.dummy_library = [
            Track(), Track(), needle, Track()]
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'addid "dummy://foo" "6"')
        self.assertEqualResponse(u'ACK [2@0] {addid} Bad song index')

    def test_addid_with_uri_not_found_in_library_should_ack(self):
        self.sendRequest(u'addid "dummy://foo"')
        self.assertEqualResponse(u'ACK [50@0] {addid} No such song')

    def test_clear(self):
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'clear')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 0)
        self.assertEqual(self.backend.playback.current_track.get(), None)
        self.assertInResponse(u'OK')

    def test_delete_songpos(self):
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'delete "%d"' %
            self.backend.current_playlist.cp_tracks.get()[2][0])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 4)
        self.assertInResponse(u'OK')

    def test_delete_songpos_out_of_bounds(self):
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'delete "5"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)
        self.assertEqualResponse(u'ACK [2@0] {delete} Bad song index')

    def test_delete_open_range(self):
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'delete "1:"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 1)
        self.assertInResponse(u'OK')

    def test_delete_closed_range(self):
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'delete "1:3"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 3)
        self.assertInResponse(u'OK')

    def test_delete_range_out_of_bounds(self):
        self.backend.current_playlist.append(
            [Track(), Track(), Track(), Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)

        self.sendRequest(u'delete "5:7"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 5)
        self.assertEqualResponse(u'ACK [2@0] {delete} Bad song index')

    def test_deleteid(self):
        self.backend.current_playlist.append([Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 2)

        self.sendRequest(u'deleteid "1"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 1)
        self.assertInResponse(u'OK')

    def test_deleteid_does_not_exist(self):
        self.backend.current_playlist.append([Track(), Track()])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 2)

        self.sendRequest(u'deleteid "12345"')
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 2)
        self.assertEqualResponse(u'ACK [50@0] {deleteid} No such song')

    def test_move_songpos(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'move "1" "0"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'b')
        self.assertEqual(tracks[1].name, 'a')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse(u'OK')

    def test_move_open_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'move "2:" "0"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'c')
        self.assertEqual(tracks[1].name, 'd')
        self.assertEqual(tracks[2].name, 'e')
        self.assertEqual(tracks[3].name, 'f')
        self.assertEqual(tracks[4].name, 'a')
        self.assertEqual(tracks[5].name, 'b')
        self.assertInResponse(u'OK')

    def test_move_closed_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'move "1:3" "0"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'b')
        self.assertEqual(tracks[1].name, 'c')
        self.assertEqual(tracks[2].name, 'a')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse(u'OK')

    def test_moveid(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'moveid "4" "2"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'b')
        self.assertEqual(tracks[2].name, 'e')
        self.assertEqual(tracks[3].name, 'c')
        self.assertEqual(tracks[4].name, 'd')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse(u'OK')

    def test_playlist_returns_same_as_playlistinfo(self):
        playlist_response = self.sendRequest(u'playlist')
        playlistinfo_response = self.sendRequest(u'playlistinfo')
        self.assertEqual(playlist_response, playlistinfo_response)

    def test_playlistfind(self):
        self.sendRequest(u'playlistfind "tag" "needle"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_playlistfind_by_filename_not_in_current_playlist(self):
        self.sendRequest(u'playlistfind "filename" "file:///dev/null"')
        self.assertEqualResponse(u'OK')

    def test_playlistfind_by_filename_without_quotes(self):
        self.sendRequest(u'playlistfind filename "file:///dev/null"')
        self.assertEqualResponse(u'OK')

    def test_playlistfind_by_filename_in_current_playlist(self):
        self.backend.current_playlist.append([
            Track(uri='file:///exists')])

        self.sendRequest( u'playlistfind filename "file:///exists"')
        self.assertInResponse(u'file: file:///exists')
        self.assertInResponse(u'Id: 0')
        self.assertInResponse(u'Pos: 0')
        self.assertInResponse(u'OK')

    def test_playlistid_without_songid(self):
        self.backend.current_playlist.append([Track(name='a'), Track(name='b')])

        self.sendRequest(u'playlistid')
        self.assertInResponse(u'Title: a')
        self.assertInResponse(u'Title: b')
        self.assertInResponse(u'OK')

    def test_playlistid_with_songid(self):
        self.backend.current_playlist.append([Track(name='a'), Track(name='b')])

        self.sendRequest(u'playlistid "1"')
        self.assertNotInResponse(u'Title: a')
        self.assertNotInResponse(u'Id: 0')
        self.assertInResponse(u'Title: b')
        self.assertInResponse(u'Id: 1')
        self.assertInResponse(u'OK')

    def test_playlistid_with_not_existing_songid_fails(self):
        self.backend.current_playlist.append([Track(name='a'), Track(name='b')])

        self.sendRequest(u'playlistid "25"')
        self.assertEqualResponse(u'ACK [50@0] {playlistid} No such song')

    def test_playlistinfo_without_songpos_or_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'playlistinfo')
        self.assertInResponse(u'Title: a')
        self.assertInResponse(u'Pos: 0')
        self.assertInResponse(u'Title: b')
        self.assertInResponse(u'Pos: 1')
        self.assertInResponse(u'Title: c')
        self.assertInResponse(u'Pos: 2')
        self.assertInResponse(u'Title: d')
        self.assertInResponse(u'Pos: 3')
        self.assertInResponse(u'Title: e')
        self.assertInResponse(u'Pos: 4')
        self.assertInResponse(u'Title: f')
        self.assertInResponse(u'Pos: 5')
        self.assertInResponse(u'OK')

    def test_playlistinfo_with_songpos(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'playlistinfo "4"')
        self.assertNotInResponse(u'Title: a')
        self.assertNotInResponse(u'Pos: 0')
        self.assertNotInResponse(u'Title: b')
        self.assertNotInResponse(u'Pos: 1')
        self.assertNotInResponse(u'Title: c')
        self.assertNotInResponse(u'Pos: 2')
        self.assertNotInResponse(u'Title: d')
        self.assertNotInResponse(u'Pos: 3')
        self.assertInResponse(u'Title: e')
        self.assertInResponse(u'Pos: 4')
        self.assertNotInResponse(u'Title: f')
        self.assertNotInResponse(u'Pos: 5')
        self.assertInResponse(u'OK')

    def test_playlistinfo_with_negative_songpos_same_as_playlistinfo(self):
        response1 = self.sendRequest(u'playlistinfo "-1"')
        response2 = self.sendRequest(u'playlistinfo')
        self.assertEqual(response1, response2)

    def test_playlistinfo_with_open_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'playlistinfo "2:"')
        self.assertNotInResponse(u'Title: a')
        self.assertNotInResponse(u'Pos: 0')
        self.assertNotInResponse(u'Title: b')
        self.assertNotInResponse(u'Pos: 1')
        self.assertInResponse(u'Title: c')
        self.assertInResponse(u'Pos: 2')
        self.assertInResponse(u'Title: d')
        self.assertInResponse(u'Pos: 3')
        self.assertInResponse(u'Title: e')
        self.assertInResponse(u'Pos: 4')
        self.assertInResponse(u'Title: f')
        self.assertInResponse(u'Pos: 5')
        self.assertInResponse(u'OK')

    def test_playlistinfo_with_closed_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'playlistinfo "2:4"')
        self.assertNotInResponse(u'Title: a')
        self.assertNotInResponse(u'Title: b')
        self.assertInResponse(u'Title: c')
        self.assertInResponse(u'Title: d')
        self.assertNotInResponse(u'Title: e')
        self.assertNotInResponse(u'Title: f')
        self.assertInResponse(u'OK')

    def test_playlistinfo_with_too_high_start_of_range_returns_arg_error(self):
        self.sendRequest(u'playlistinfo "10:20"')
        self.assertEqualResponse(u'ACK [2@0] {playlistinfo} Bad song index')

    def test_playlistinfo_with_too_high_end_of_range_returns_ok(self):
        self.sendRequest(u'playlistinfo "0:20"')
        self.assertInResponse(u'OK')

    def test_playlistsearch(self):
        self.sendRequest( u'playlistsearch "any" "needle"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_playlistsearch_without_quotes(self):
        self.sendRequest(u'playlistsearch any "needle"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_plchanges(self):
        self.backend.current_playlist.append(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.sendRequest(u'plchanges "0"')
        self.assertInResponse(u'Title: a')
        self.assertInResponse(u'Title: b')
        self.assertInResponse(u'Title: c')
        self.assertInResponse(u'OK')

    def test_plchanges_with_minus_one_returns_entire_playlist(self):
        self.backend.current_playlist.append(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.sendRequest(u'plchanges "-1"')
        self.assertInResponse(u'Title: a')
        self.assertInResponse(u'Title: b')
        self.assertInResponse(u'Title: c')
        self.assertInResponse(u'OK')

    def test_plchanges_without_quotes_works(self):
        self.backend.current_playlist.append(
            [Track(name='a'), Track(name='b'), Track(name='c')])

        self.sendRequest(u'plchanges 0')
        self.assertInResponse(u'Title: a')
        self.assertInResponse(u'Title: b')
        self.assertInResponse(u'Title: c')
        self.assertInResponse(u'OK')

    def test_plchangesposid(self):
        self.backend.current_playlist.append([Track(), Track(), Track()])

        self.sendRequest(u'plchangesposid "0"')
        cp_tracks = self.backend.current_playlist.cp_tracks.get()
        self.assertInResponse(u'cpos: 0')
        self.assertInResponse(u'Id: %d' % cp_tracks[0][0])
        self.assertInResponse(u'cpos: 2')
        self.assertInResponse(u'Id: %d' % cp_tracks[1][0])
        self.assertInResponse(u'cpos: 2')
        self.assertInResponse(u'Id: %d' % cp_tracks[2][0])
        self.assertInResponse(u'OK')

    def test_shuffle_without_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.backend.current_playlist.version.get()

        self.sendRequest(u'shuffle')
        self.assert_(version < self.backend.current_playlist.version.get())
        self.assertInResponse(u'OK')

    def test_shuffle_with_open_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.backend.current_playlist.version.get()

        self.sendRequest(u'shuffle "4:"')
        self.assert_(version < self.backend.current_playlist.version.get())
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'b')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertInResponse(u'OK')

    def test_shuffle_with_closed_range(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])
        version = self.backend.current_playlist.version.get()

        self.sendRequest(u'shuffle "1:3"')
        self.assert_(version < self.backend.current_playlist.version.get())
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'e')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse(u'OK')

    def test_swap(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'swap "1" "4"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'e')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'b')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse(u'OK')

    def test_swapid(self):
        self.backend.current_playlist.append([
            Track(name='a'), Track(name='b'), Track(name='c'),
            Track(name='d'), Track(name='e'), Track(name='f'),
        ])

        self.sendRequest(u'swapid "1" "4"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(tracks[0].name, 'a')
        self.assertEqual(tracks[1].name, 'e')
        self.assertEqual(tracks[2].name, 'c')
        self.assertEqual(tracks[3].name, 'd')
        self.assertEqual(tracks[4].name, 'b')
        self.assertEqual(tracks[5].name, 'f')
        self.assertInResponse(u'OK')
