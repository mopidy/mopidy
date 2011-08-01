import datetime

from mopidy.models import Track, Playlist

from tests.frontends.mpd import protocol


class StoredPlaylistsHandlerTest(protocol.BaseTestCase):
    def test_listplaylist(self):
        self.backend.stored_playlists.playlists = [
            Playlist(name='name', tracks=[Track(uri='file:///dev/urandom')])]

        self.sendRequest(u'listplaylist "name"')
        self.assertInResponse(u'file: file:///dev/urandom')
        self.assertInResponse(u'OK')

    def test_listplaylist_fails_if_no_playlist_is_found(self):
        self.sendRequest(u'listplaylist "name"')
        self.assertEqualResponse(u'ACK [50@0] {listplaylist} No such playlist')

    def test_listplaylistinfo(self):
        self.backend.stored_playlists.playlists = [
            Playlist(name='name', tracks=[Track(uri='file:///dev/urandom')])]

        self.sendRequest(u'listplaylistinfo "name"')
        self.assertInResponse(u'file: file:///dev/urandom')
        self.assertInResponse(u'Track: 0')
        self.assertNotInResponse(u'Pos: 0')
        self.assertInResponse(u'OK')

    def test_listplaylistinfo_fails_if_no_playlist_is_found(self):
        self.sendRequest(u'listplaylistinfo "name"')
        self.assertEqualResponse(
            u'ACK [50@0] {listplaylistinfo} No such playlist')

    def test_listplaylists(self):
        last_modified = datetime.datetime(2001, 3, 17, 13, 41, 17, 12345)
        self.backend.stored_playlists.playlists = [Playlist(name='a',
            last_modified=last_modified)]

        self.sendRequest(u'listplaylists')
        self.assertInResponse(u'playlist: a')
        # Date without microseconds and with time zone information
        self.assertInResponse(u'Last-Modified: 2001-03-17T13:41:17Z')
        self.assertInResponse(u'OK')

    def test_load_known_playlist_appends_to_current_playlist(self):
        self.backend.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.backend.current_playlist.tracks.get()), 2)
        self.backend.stored_playlists.playlists = [Playlist(name='A-list',
            tracks=[Track(uri='c'), Track(uri='d'), Track(uri='e')])]

        self.sendRequest(u'load "A-list"')
        tracks = self.backend.current_playlist.tracks.get()
        self.assertEqual(5, len(tracks))
        self.assertEqual('a', tracks[0].uri)
        self.assertEqual('b', tracks[1].uri)
        self.assertEqual('c', tracks[2].uri)
        self.assertEqual('d', tracks[3].uri)
        self.assertEqual('e', tracks[4].uri)
        self.assertInResponse(u'OK')

    def test_load_unknown_playlist_acks(self):
        self.sendRequest(u'load "unknown playlist"')
        self.assertEqual(0, len(self.backend.current_playlist.tracks.get()))
        self.assertEqualResponse(u'ACK [50@0] {load} No such playlist')

    def test_playlistadd(self):
        self.sendRequest(u'playlistadd "name" "file:///dev/urandom"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_playlistclear(self):
        self.sendRequest(u'playlistclear "name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_playlistdelete(self):
        self.sendRequest(u'playlistdelete "name" "5"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_playlistmove(self):
        self.sendRequest(u'playlistmove "name" "5" "10"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_rename(self):
        self.sendRequest(u'rename "old_name" "new_name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_rm(self):
        self.sendRequest(u'rm "name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_save(self):
        self.sendRequest(u'save "name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')
