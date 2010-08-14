import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import frontend
from mopidy.mixers.dummy import DummyMixer

class MusicDatabaseHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend(mixer_class=DummyMixer)
        self.h = frontend.MpdFrontend(backend=self.b)

    def test_count(self):
        result = self.h.handle_request(u'count "tag" "needle"')
        self.assert_(u'songs: 0' in result)
        self.assert_(u'playtime: 0' in result)
        self.assert_(u'OK' in result)

    def test_find_album(self):
        result = self.h.handle_request(u'find "album" "what"')
        self.assert_(u'OK' in result)

    def test_find_album_without_quotes(self):
        result = self.h.handle_request(u'find album "what"')
        self.assert_(u'OK' in result)

    def test_find_artist(self):
        result = self.h.handle_request(u'find "artist" "what"')
        self.assert_(u'OK' in result)

    def test_find_artist_without_quotes(self):
        result = self.h.handle_request(u'find artist "what"')
        self.assert_(u'OK' in result)

    def test_find_title(self):
        result = self.h.handle_request(u'find "title" "what"')
        self.assert_(u'OK' in result)

    def test_find_title_without_quotes(self):
        result = self.h.handle_request(u'find title "what"')
        self.assert_(u'OK' in result)

    def test_find_else_should_fail(self):
        result = self.h.handle_request(u'find "somethingelse" "what"')
        self.assertEqual(result[0], u'ACK [2@0] {find} incorrect arguments')

    def test_find_album_and_artist(self):
        result = self.h.handle_request(
            u'find album "album_what" artist "artist_what"')
        self.assert_(u'OK' in result)

    def test_findadd(self):
        result = self.h.handle_request(u'findadd "album" "what"')
        self.assert_(u'OK' in result)

    def test_list_artist(self):
        result = self.h.handle_request(u'list "artist"')
        self.assert_(u'OK' in result)

    def test_list_artist_without_quotes(self):
        result = self.h.handle_request(u'list artist')
        self.assert_(u'OK' in result)

    def test_list_artist_without_quotes_and_capitalized(self):
        result = self.h.handle_request(u'list Artist')
        self.assert_(u'OK' in result)

    def test_list_artist_with_artist_should_fail(self):
        result = self.h.handle_request(u'list "artist" "anartist"')
        self.assertEqual(result[0], u'ACK [2@0] {list} incorrect arguments')

    def test_list_album_without_artist(self):
        result = self.h.handle_request(u'list "album"')
        self.assert_(u'OK' in result)

    def test_list_album_with_artist(self):
        result = self.h.handle_request(u'list "album" "anartist"')
        self.assert_(u'OK' in result)

    def test_list_album_artist_with_artist_without_quotes(self):
        result = self.h.handle_request(u'list album artist "anartist"')
        self.assert_(u'OK' in result)

    def test_listall(self):
        result = self.h.handle_request(u'listall "file:///dev/urandom"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_listallinfo(self):
        result = self.h.handle_request(u'listallinfo "file:///dev/urandom"')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_lsinfo_without_path_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEqual(lsinfo_result, listplaylists_result)

    def test_lsinfo_with_empty_path_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo ""')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEqual(lsinfo_result, listplaylists_result)

    def test_lsinfo_for_root_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo "/"')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEqual(lsinfo_result, listplaylists_result)

    def test_search_album(self):
        result = self.h.handle_request(u'search "album" "analbum"')
        self.assert_(u'OK' in result)

    def test_search_album_without_quotes(self):
        result = self.h.handle_request(u'search album "analbum"')
        self.assert_(u'OK' in result)

    def test_search_artist(self):
        result = self.h.handle_request(u'search "artist" "anartist"')
        self.assert_(u'OK' in result)

    def test_search_artist_without_quotes(self):
        result = self.h.handle_request(u'search artist "anartist"')
        self.assert_(u'OK' in result)

    def test_search_filename(self):
        result = self.h.handle_request(u'search "filename" "afilename"')
        self.assert_(u'OK' in result)

    def test_search_filename_without_quotes(self):
        result = self.h.handle_request(u'search filename "afilename"')
        self.assert_(u'OK' in result)

    def test_search_title(self):
        result = self.h.handle_request(u'search "title" "atitle"')
        self.assert_(u'OK' in result)

    def test_search_title_without_quotes(self):
        result = self.h.handle_request(u'search title "atitle"')
        self.assert_(u'OK' in result)

    def test_search_any(self):
        result = self.h.handle_request(u'search "any" "anything"')
        self.assert_(u'OK' in result)

    def test_search_any_without_quotes(self):
        result = self.h.handle_request(u'search any "anything"')
        self.assert_(u'OK' in result)

    def test_search_else_should_fail(self):
        result = self.h.handle_request(u'search "sometype" "something"')
        self.assertEqual(result[0], u'ACK [2@0] {search} incorrect arguments')

    def test_update_without_uri(self):
        result = self.h.handle_request(u'update')
        self.assert_(u'OK' in result)
        self.assert_(u'updating_db: 0' in result)

    def test_update_with_uri(self):
        result = self.h.handle_request(u'update "file:///dev/urandom"')
        self.assert_(u'OK' in result)
        self.assert_(u'updating_db: 0' in result)

    def test_rescan_without_uri(self):
        result = self.h.handle_request(u'rescan')
        self.assert_(u'OK' in result)
        self.assert_(u'updating_db: 0' in result)

    def test_rescan_with_uri(self):
        result = self.h.handle_request(u'rescan "file:///dev/urandom"')
        self.assert_(u'OK' in result)
        self.assert_(u'updating_db: 0' in result)
