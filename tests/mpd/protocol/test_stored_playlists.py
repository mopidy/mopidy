from __future__ import absolute_import, unicode_literals

import mock

from mopidy.models import Playlist, Track
from mopidy.mpd.protocol import stored_playlists

from tests.mpd import protocol


class PlaylistsHandlerTest(protocol.BaseTestCase):

    def test_listplaylist(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])])

        self.send_request('listplaylist "name"')
        self.assertInResponse('file: dummy:a')
        self.assertInResponse('OK')

    def test_listplaylist_without_quotes(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])])

        self.send_request('listplaylist name')
        self.assertInResponse('file: dummy:a')
        self.assertInResponse('OK')

    def test_listplaylist_fails_if_no_playlist_is_found(self):
        self.send_request('listplaylist "name"')
        self.assertEqualResponse('ACK [50@0] {listplaylist} No such playlist')

    def test_listplaylist_duplicate(self):
        playlist1 = Playlist(name='a', uri='dummy:a1', tracks=[Track(uri='b')])
        playlist2 = Playlist(name='a', uri='dummy:a2', tracks=[Track(uri='c')])
        self.backend.playlists.set_dummy_playlists([playlist1, playlist2])

        self.send_request('listplaylist "a [2]"')
        self.assertInResponse('file: c')
        self.assertInResponse('OK')

    def test_listplaylistinfo(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])])

        self.send_request('listplaylistinfo "name"')
        self.assertInResponse('file: dummy:a')
        self.assertNotInResponse('Track: 0')
        self.assertNotInResponse('Pos: 0')
        self.assertInResponse('OK')

    def test_listplaylistinfo_without_quotes(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:name', tracks=[Track(uri='dummy:a')])])

        self.send_request('listplaylistinfo name')
        self.assertInResponse('file: dummy:a')
        self.assertNotInResponse('Track: 0')
        self.assertNotInResponse('Pos: 0')
        self.assertInResponse('OK')

    def test_listplaylistinfo_fails_if_no_playlist_is_found(self):
        self.send_request('listplaylistinfo "name"')
        self.assertEqualResponse(
            'ACK [50@0] {listplaylistinfo} No such playlist')

    def test_listplaylistinfo_duplicate(self):
        playlist1 = Playlist(name='a', uri='dummy:a1', tracks=[Track(uri='b')])
        playlist2 = Playlist(name='a', uri='dummy:a2', tracks=[Track(uri='c')])
        self.backend.playlists.set_dummy_playlists([playlist1, playlist2])

        self.send_request('listplaylistinfo "a [2]"')
        self.assertInResponse('file: c')
        self.assertNotInResponse('Track: 0')
        self.assertNotInResponse('Pos: 0')
        self.assertInResponse('OK')

    @mock.patch.object(stored_playlists, '_get_last_modified')
    def test_listplaylists(self, last_modified_mock):
        last_modified_mock.return_value = '2015-08-05T22:51:06Z'
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='a', uri='dummy:a')])

        self.send_request('listplaylists')
        self.assertInResponse('playlist: a')
        # Date without milliseconds and with time zone information
        self.assertInResponse('Last-Modified: 2015-08-05T22:51:06Z')
        self.assertInResponse('OK')

    def test_listplaylists_duplicate(self):
        playlist1 = Playlist(name='a', uri='dummy:a1')
        playlist2 = Playlist(name='a', uri='dummy:a2')
        self.backend.playlists.set_dummy_playlists([playlist1, playlist2])

        self.send_request('listplaylists')
        self.assertInResponse('playlist: a')
        self.assertInResponse('playlist: a [2]')
        self.assertInResponse('OK')

    def test_listplaylists_ignores_playlists_without_name(self):
        last_modified = 1390942873222
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='', uri='dummy:', last_modified=last_modified)])

        self.send_request('listplaylists')
        self.assertNotInResponse('playlist: ')
        self.assertInResponse('OK')

    def test_listplaylists_replaces_newline_with_space(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='a\n', uri='dummy:')])
        self.send_request('listplaylists')
        self.assertInResponse('playlist: a ')
        self.assertNotInResponse('playlist: a\n')
        self.assertInResponse('OK')

    def test_listplaylists_replaces_carriage_return_with_space(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='a\r', uri='dummy:')])
        self.send_request('listplaylists')
        self.assertInResponse('playlist: a ')
        self.assertNotInResponse('playlist: a\r')
        self.assertInResponse('OK')

    def test_listplaylists_replaces_forward_slash_with_pipe(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='a/b', uri='dummy:')])
        self.send_request('listplaylists')
        self.assertInResponse('playlist: a|b')
        self.assertNotInResponse('playlist: a/b')
        self.assertInResponse('OK')

    def test_load_appends_to_tracklist(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:c'),
            Track(uri='dummy:d'),
            Track(uri='dummy:e'),
        ]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=['dummy:a', 'dummy:b']).get()

        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='A-list', uri='dummy:A-list', tracks=tracks[2:])])

        self.send_request('load "A-list"')

        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(5, len(tracks))
        self.assertEqual('dummy:a', tracks[0].uri)
        self.assertEqual('dummy:b', tracks[1].uri)
        self.assertEqual('dummy:c', tracks[2].uri)
        self.assertEqual('dummy:d', tracks[3].uri)
        self.assertEqual('dummy:e', tracks[4].uri)
        self.assertInResponse('OK')

    def test_load_with_range_loads_part_of_playlist(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:c'),
            Track(uri='dummy:d'),
            Track(uri='dummy:e'),
        ]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=['dummy:a', 'dummy:b']).get()

        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='A-list', uri='dummy:A-list', tracks=tracks[2:])])

        self.send_request('load "A-list" "1:2"')

        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(3, len(tracks))
        self.assertEqual('dummy:a', tracks[0].uri)
        self.assertEqual('dummy:b', tracks[1].uri)
        self.assertEqual('dummy:d', tracks[2].uri)
        self.assertInResponse('OK')

    def test_load_with_range_without_end_loads_rest_of_playlist(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:c'),
            Track(uri='dummy:d'),
            Track(uri='dummy:e'),
        ]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=['dummy:a', 'dummy:b']).get()

        self.assertEqual(len(self.core.tracklist.tracks.get()), 2)
        self.backend.playlists.set_dummy_playlists([
            Playlist(name='A-list', uri='dummy:A-list', tracks=tracks[2:])])

        self.send_request('load "A-list" "1:"')

        tracks = self.core.tracklist.tracks.get()
        self.assertEqual(4, len(tracks))
        self.assertEqual('dummy:a', tracks[0].uri)
        self.assertEqual('dummy:b', tracks[1].uri)
        self.assertEqual('dummy:d', tracks[2].uri)
        self.assertEqual('dummy:e', tracks[3].uri)
        self.assertInResponse('OK')

    def test_load_unknown_playlist_acks(self):
        self.send_request('load "unknown playlist"')
        self.assertEqual(0, len(self.core.tracklist.tracks.get()))
        self.assertEqualResponse('ACK [50@0] {load} No such playlist')

    def test_playlistadd(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
        ]
        self.backend.library.dummy_library = tracks
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:a1', tracks=[tracks[0]])])

        self.send_request('playlistadd "name" "dummy:b"')

        self.assertInResponse('OK')
        self.assertEqual(
            2, len(self.backend.playlists.get_items('dummy:a1').get()))

    def test_playlistadd_creates_playlist(self):
        tracks = [
            Track(uri='dummy:a'),
        ]
        self.backend.library.dummy_library = tracks
        self.send_request('playlistadd "name" "dummy:a"')
        self.assertInResponse('OK')
        self.assertNotEqual(
            None, self.backend.playlists.lookup('dummy:name').get())

    def test_playlistclear(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:a1', tracks=[Track(uri='b')])])

        self.send_request('playlistclear "name"')
        self.assertInResponse('OK')
        self.assertEqual(
            0, len(self.backend.playlists.get_items("dummy:a1").get()))

    def test_playlistclear_creates_playlist(self):
        self.send_request('playlistclear "name"')
        self.assertInResponse('OK')
        self.assertNotEqual(
            None, self.backend.playlists.lookup("dummy:name").get())

    def test_playlistdelete(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:c'),
        ]   # len() == 3
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:a1', tracks=tracks)])

        self.send_request('playlistdelete "name" "2"')
        self.assertInResponse('OK')
        self.assertEqual(
            2, len(self.backend.playlists.get_items("dummy:a1").get()))

    def test_playlistmove(self):
        tracks = [
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:c')    # this one is getting moved to top
        ]
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:a1', tracks=tracks)])
        self.send_request('playlistmove "name" "2" "0"')
        self.assertInResponse('OK')
        self.assertEqual(
            "dummy:c",
            self.backend.playlists.get_items("dummy:a1").get()[0].uri)

    def test_rename(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='old_name', uri='dummy:a1', tracks=[Track(uri='b')])])
        self.send_request('rename "old_name" "new_name"')
        self.assertInResponse('OK')
        self.assertIsNotNone(self.backend.playlists.lookup("dummy:new_name").get())

    def test_rm(self):
        self.backend.playlists.set_dummy_playlists([
            Playlist(
                name='name', uri='dummy:a1', tracks=[Track(uri='b')])])
        self.send_request('rm "name"')
        self.assertInResponse('OK')
        self.assertEqual(
            None, self.backend.playlists.lookup("dummy:a1").get())

    def test_save(self):
        self.send_request('save "name"')
        self.assertInResponse('OK')
        self.assertNotEqual(
            None, self.backend.playlists.lookup("dummy:name").get())
