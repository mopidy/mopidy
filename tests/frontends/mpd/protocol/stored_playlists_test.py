from __future__ import unicode_literals

import datetime

from mopidy.models import Track, Playlist

from tests.frontends.mpd import protocol


class PlaylistsHandlerTest(protocol.BaseTestCase):
    def test_listplaylist(self):
        self.backend.playlists.playlists = [
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])]

        self.sendRequest('listplaylist "name"')
        self.assertInResponse('file: dummy:a')
        self.assertInResponse('OK')

    def test_listplaylist_without_quotes(self):
        self.backend.playlists.playlists = [
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])]

        self.sendRequest('listplaylist name')
        self.assertInResponse('file: dummy:a')
        self.assertInResponse('OK')

    def test_listplaylist_fails_if_no_playlist_is_found(self):
        self.sendRequest('listplaylist "name"')
        self.assertEqualResponse('ACK [50@0] {listplaylist} No such playlist')

    def test_listplaylist_duplicate(self):
        playlist1 = Playlist(name='a', uri='dummy:a1', tracks=[Track(uri='b')])
        playlist2 = Playlist(name='a', uri='dummy:a2', tracks=[Track(uri='c')])
        self.backend.playlists.playlists = [playlist1, playlist2]

        self.sendRequest('listplaylist "a [2]"')
        self.assertInResponse('file: c')
        self.assertInResponse('OK')

    def test_listplaylistinfo(self):
        self.backend.playlists.playlists = [
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])]

        self.sendRequest('listplaylistinfo "name"')
        self.assertInResponse('file: dummy:a')
        self.assertInResponse('Track: 0')
        self.assertNotInResponse('Pos: 0')
        self.assertInResponse('OK')

    def test_listplaylistinfo_without_quotes(self):
        self.backend.playlists.playlists = [
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])]

        self.sendRequest('listplaylistinfo name')
        self.assertInResponse('file: dummy:a')
        self.assertInResponse('Track: 0')
        self.assertNotInResponse('Pos: 0')
        self.assertInResponse('OK')

    def test_listplaylistinfo_fails_if_no_playlist_is_found(self):
        self.sendRequest('listplaylistinfo "name"')
        self.assertEqualResponse(
            'ACK [50@0] {listplaylistinfo} No such playlist')

    def test_listplaylistinfo_duplicate(self):
        playlist1 = Playlist(name='a', uri='dummy:a1', tracks=[Track(uri='b')])
        playlist2 = Playlist(name='a', uri='dummy:a2', tracks=[Track(uri='c')])
        self.backend.playlists.playlists = [playlist1, playlist2]

        self.sendRequest('listplaylistinfo "a [2]"')
        self.assertInResponse('file: c')
        self.assertInResponse('Track: 0')
        self.assertNotInResponse('Pos: 0')
        self.assertInResponse('OK')

    def test_listplaylists(self):
        last_modified = datetime.datetime(2001, 3, 17, 13, 41, 17, 12345)
        self.backend.playlists.playlists = [
            Playlist(name='a', uri='dummy:a', last_modified=last_modified)]

        self.sendRequest('listplaylists')
        self.assertInResponse('playlist: a')
        # Date without microseconds and with time zone information
        self.assertInResponse('Last-Modified: 2001-03-17T13:41:17Z')
        self.assertInResponse('OK')

    def test_listplaylists_duplicate(self):
        playlist1 = Playlist(name='a', uri='dummy:a1')
        playlist2 = Playlist(name='a', uri='dummy:a2')
        self.backend.playlists.playlists = [playlist1, playlist2]

        self.sendRequest('listplaylists')
        self.assertInResponse('playlist: a')
        self.assertInResponse('playlist: a [2]')
        self.assertInResponse('OK')

    def test_listplaylists_ignores_playlists_without_name(self):
        last_modified = datetime.datetime(2001, 3, 17, 13, 41, 17, 12345)
        self.backend.playlists.playlists = [
            Playlist(name='', uri='dummy:', last_modified=last_modified)]

        self.sendRequest('listplaylists')
        self.assertNotInResponse('playlist: ')
        self.assertInResponse('OK')

    def test_listplaylists_replaces_newline_with_space(self):
        self.backend.playlists.playlists = [
            Playlist(name='a\n', uri='dummy:')]
        self.sendRequest('listplaylists')
        self.assertInResponse('playlist: a ')
        self.assertNotInResponse('playlist: a\n')
        self.assertInResponse('OK')

    def test_listplaylists_replaces_carriage_return_with_space(self):
        self.backend.playlists.playlists = [
            Playlist(name='a\r', uri='dummy:')]
        self.sendRequest('listplaylists')
        self.assertInResponse('playlist: a ')
        self.assertNotInResponse('playlist: a\r')
        self.assertInResponse('OK')

    def test_listplaylists_replaces_forward_slash_with_space(self):
        self.backend.playlists.playlists = [
            Playlist(name='a/', uri='dummy:')]
        self.sendRequest('listplaylists')
        self.assertInResponse('playlist: a ')
        self.assertNotInResponse('playlist: a/')
        self.assertInResponse('OK')

    def test_load_appends_to_tracklist(self):
        self.core.tracklist.add([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.backend.playlists.playlists = [
            Playlist(name='A-list', uri='dummy:A-list', tracks=[
                Track(uri='c'), Track(uri='d'), Track(uri='e')])]

        self.sendRequest('load "A-list"')

        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(5, len(tracks))
        self.assertEqual('a', tracks[0].uri)
        self.assertEqual('b', tracks[1].uri)
        self.assertEqual('c', tracks[2].uri)
        self.assertEqual('d', tracks[3].uri)
        self.assertEqual('e', tracks[4].uri)
        self.assertInResponse('OK')

    def test_load_with_range_loads_part_of_playlist(self):
        self.core.tracklist.add([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.backend.playlists.playlists = [
            Playlist(name='A-list', uri='dummy:A-list', tracks=[
                Track(uri='c'), Track(uri='d'), Track(uri='e')])]

        self.sendRequest('load "A-list" "1:2"')

        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(3, len(tracks))
        self.assertEqual('a', tracks[0].uri)
        self.assertEqual('b', tracks[1].uri)
        self.assertEqual('d', tracks[2].uri)
        self.assertInResponse('OK')

    def test_load_with_range_without_end_loads_rest_of_playlist(self):
        self.core.tracklist.add([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.backend.playlists.playlists = [
            Playlist(name='A-list', uri='dummy:A-list', tracks=[
                Track(uri='c'), Track(uri='d'), Track(uri='e')])]

        self.sendRequest('load "A-list" "1:"')

        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(4, len(tracks))
        self.assertEqual('a', tracks[0].uri)
        self.assertEqual('b', tracks[1].uri)
        self.assertEqual('d', tracks[2].uri)
        self.assertEqual('e', tracks[3].uri)
        self.assertInResponse('OK')

    def test_load_unknown_playlist_acks(self):
        self.sendRequest('load "unknown playlist"')
        self.assertEqual(0, len(self.core.tracklist.tracks.get()))
        self.assertEqualResponse('ACK [50@0] {load} No such playlist')

    def test_playlistadd(self):
        self.sendRequest('playlistadd "name" "dummy:a"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_playlistclear(self):
        self.sendRequest('playlistclear "name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_playlistdelete(self):
        self.sendRequest('playlistdelete "name" "5"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_playlistmove(self):
        self.sendRequest('playlistmove "name" "5" "10"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_rename(self):
        self.sendRequest('rename "old_name" "new_name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_rm(self):
        self.sendRequest('rm "name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_save(self):
        self.sendRequest('save "name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')
