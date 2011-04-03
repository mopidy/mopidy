import datetime as dt
import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer
from mopidy.models import Track, Playlist

class StoredPlaylistsHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_listplaylist(self):
        self.b.stored_playlists.playlists = [
            Playlist(name='name', tracks=[Track(uri='file:///dev/urandom')])]
        result = self.h.handle_request(u'listplaylist "name"')
        self.assert_(u'file: file:///dev/urandom' in result)
        self.assert_(u'OK' in result)

    def test_listplaylist_fails_if_no_playlist_is_found(self):
        result = self.h.handle_request(u'listplaylist "name"')
        self.assertEqual(result[0],
            u'ACK [50@0] {listplaylist} No such playlist')

    def test_listplaylistinfo(self):
        self.b.stored_playlists.playlists = [
            Playlist(name='name', tracks=[Track(uri='file:///dev/urandom')])]
        result = self.h.handle_request(u'listplaylistinfo "name"')
        self.assert_(u'file: file:///dev/urandom' in result)
        self.assert_(u'Track: 0' in result)
        self.assert_(u'Pos: 0' not in result)
        self.assert_(u'OK' in result)

    def test_listplaylistinfo_fails_if_no_playlist_is_found(self):
        result = self.h.handle_request(u'listplaylistinfo "name"')
        self.assertEqual(result[0],
            u'ACK [50@0] {listplaylistinfo} No such playlist')

    def test_listplaylists(self):
        last_modified = dt.datetime(2001, 3, 17, 13, 41, 17, 12345)
        self.b.stored_playlists.playlists = [Playlist(name='a',
            last_modified=last_modified)]
        result = self.h.handle_request(u'listplaylists')
        self.assert_(u'playlist: a' in result)
        # Date without microseconds and with time zone information
        self.assert_(u'Last-Modified: 2001-03-17T13:41:17Z' in result)
        self.assert_(u'OK' in result)

    def test_load_known_playlist_appends_to_current_playlist(self):
        self.b.current_playlist.append([Track(uri='a'), Track(uri='b')])
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 2)
        self.b.stored_playlists.playlists = [Playlist(name='A-list',
            tracks=[Track(uri='c'), Track(uri='d'), Track(uri='e')])]
        result = self.h.handle_request(u'load "A-list"')
        self.assert_(u'OK' in result)
        tracks = self.b.current_playlist.tracks.get()
        self.assertEqual(len(tracks), 5)
        self.assertEqual(tracks[0].uri, 'a')
        self.assertEqual(tracks[1].uri, 'b')
        self.assertEqual(tracks[2].uri, 'c')
        self.assertEqual(tracks[3].uri, 'd')
        self.assertEqual(tracks[4].uri, 'e')

    def test_load_unknown_playlist_acks(self):
        result = self.h.handle_request(u'load "unknown playlist"')
        self.assert_(u'ACK [50@0] {load} No such playlist' in result)
        self.assertEqual(len(self.b.current_playlist.tracks.get()), 0)

    def test_playlistadd(self):
        result = self.h.handle_request(
            u'playlistadd "name" "file:///dev/urandom"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_playlistclear(self):
        result = self.h.handle_request(u'playlistclear "name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_playlistdelete(self):
        result = self.h.handle_request(u'playlistdelete "name" "5"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_playlistmove(self):
        result = self.h.handle_request(u'playlistmove "name" "5" "10"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_rename(self):
        result = self.h.handle_request(u'rename "old_name" "new_name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_rm(self):
        result = self.h.handle_request(u'rm "name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_save(self):
        result = self.h.handle_request(u'save "name"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)
