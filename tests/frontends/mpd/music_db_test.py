import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer

class MusicDatabaseHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_count(self):
        result = self.h.handle_request(u'count "tag" "needle"')
        self.assert_(u'songs: 0' in result)
        self.assert_(u'playtime: 0' in result)
        self.assert_(u'OK' in result)

    def test_findadd(self):
        result = self.h.handle_request(u'findadd "album" "what"')
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


class MusicDatabaseFindTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

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

    def test_find_date(self):
        result = self.h.handle_request(u'find "date" "2002-01-01"')
        self.assert_(u'OK' in result)

    def test_find_date_without_quotes(self):
        result = self.h.handle_request(u'find date "2002-01-01"')
        self.assert_(u'OK' in result)

    def test_find_date_with_capital_d_and_incomplete_date(self):
        result = self.h.handle_request(u'find Date "2005"')
        self.assert_(u'OK' in result)

    def test_find_else_should_fail(self):

        result = self.h.handle_request(u'find "somethingelse" "what"')
        self.assertEqual(result[0], u'ACK [2@0] {find} incorrect arguments')

    def test_find_album_and_artist(self):
        result = self.h.handle_request(
            u'find album "album_what" artist "artist_what"')
        self.assert_(u'OK' in result)


class MusicDatabaseListTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_list_foo_returns_ack(self):
        result = self.h.handle_request(u'list "foo"')
        self.assertEqual(result[0],
            u'ACK [2@0] {list} incorrect arguments')

    ### Artist

    def test_list_artist_with_quotes(self):
        result = self.h.handle_request(u'list "artist"')
        self.assert_(u'OK' in result)

    def test_list_artist_without_quotes(self):
        result = self.h.handle_request(u'list artist')
        self.assert_(u'OK' in result)

    def test_list_artist_without_quotes_and_capitalized(self):
        result = self.h.handle_request(u'list Artist')
        self.assert_(u'OK' in result)

    def test_list_artist_with_query_of_one_token(self):
        result = self.h.handle_request(u'list "artist" "anartist"')
        self.assertEqual(result[0],
            u'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_artist_with_unknown_field_in_query_returns_ack(self):
        result = self.h.handle_request(u'list "artist" "foo" "bar"')
        self.assertEqual(result[0],
            u'ACK [2@0] {list} not able to parse args')

    def test_list_artist_by_artist(self):
        result = self.h.handle_request(u'list "artist" "artist" "anartist"')
        self.assert_(u'OK' in result)

    def test_list_artist_by_album(self):
        result = self.h.handle_request(u'list "artist" "album" "analbum"')
        self.assert_(u'OK' in result)

    def test_list_artist_by_full_date(self):
        result = self.h.handle_request(u'list "artist" "date" "2001-01-01"')
        self.assert_(u'OK' in result)

    def test_list_artist_by_year(self):
        result = self.h.handle_request(u'list "artist" "date" "2001"')
        self.assert_(u'OK' in result)

    def test_list_artist_by_genre(self):
        result = self.h.handle_request(u'list "artist" "genre" "agenre"')
        self.assert_(u'OK' in result)

    def test_list_artist_by_artist_and_album(self):
        result = self.h.handle_request(
            u'list "artist" "artist" "anartist" "album" "analbum"')
        self.assert_(u'OK' in result)

    ### Album

    def test_list_album_with_quotes(self):
        result = self.h.handle_request(u'list "album"')
        self.assert_(u'OK' in result)

    def test_list_album_without_quotes(self):
        result = self.h.handle_request(u'list album')
        self.assert_(u'OK' in result)

    def test_list_album_without_quotes_and_capitalized(self):
        result = self.h.handle_request(u'list Album')
        self.assert_(u'OK' in result)

    def test_list_album_with_artist_name(self):
        result = self.h.handle_request(u'list "album" "anartist"')
        self.assert_(u'OK' in result)

    def test_list_album_by_artist(self):
        result = self.h.handle_request(u'list "album" "artist" "anartist"')
        self.assert_(u'OK' in result)

    def test_list_album_by_album(self):
        result = self.h.handle_request(u'list "album" "album" "analbum"')
        self.assert_(u'OK' in result)

    def test_list_album_by_full_date(self):
        result = self.h.handle_request(u'list "album" "date" "2001-01-01"')
        self.assert_(u'OK' in result)

    def test_list_album_by_year(self):
        result = self.h.handle_request(u'list "album" "date" "2001"')
        self.assert_(u'OK' in result)

    def test_list_album_by_genre(self):
        result = self.h.handle_request(u'list "album" "genre" "agenre"')
        self.assert_(u'OK' in result)

    def test_list_album_by_artist_and_album(self):
        result = self.h.handle_request(
            u'list "album" "artist" "anartist" "album" "analbum"')
        self.assert_(u'OK' in result)

    ### Date

    def test_list_date_with_quotes(self):
        result = self.h.handle_request(u'list "date"')
        self.assert_(u'OK' in result)

    def test_list_date_without_quotes(self):
        result = self.h.handle_request(u'list date')
        self.assert_(u'OK' in result)

    def test_list_date_without_quotes_and_capitalized(self):
        result = self.h.handle_request(u'list Date')
        self.assert_(u'OK' in result)

    def test_list_date_with_query_of_one_token(self):
        result = self.h.handle_request(u'list "date" "anartist"')
        self.assertEqual(result[0],
            u'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_date_by_artist(self):
        result = self.h.handle_request(u'list "date" "artist" "anartist"')
        self.assert_(u'OK' in result)

    def test_list_date_by_album(self):
        result = self.h.handle_request(u'list "date" "album" "analbum"')
        self.assert_(u'OK' in result)

    def test_list_date_by_full_date(self):
        result = self.h.handle_request(u'list "date" "date" "2001-01-01"')
        self.assert_(u'OK' in result)

    def test_list_date_by_year(self):
        result = self.h.handle_request(u'list "date" "date" "2001"')
        self.assert_(u'OK' in result)

    def test_list_date_by_genre(self):
        result = self.h.handle_request(u'list "date" "genre" "agenre"')
        self.assert_(u'OK' in result)

    def test_list_date_by_artist_and_album(self):
        result = self.h.handle_request(
            u'list "date" "artist" "anartist" "album" "analbum"')
        self.assert_(u'OK' in result)

    ### Genre

    def test_list_genre_with_quotes(self):
        result = self.h.handle_request(u'list "genre"')
        self.assert_(u'OK' in result)

    def test_list_genre_without_quotes(self):
        result = self.h.handle_request(u'list genre')
        self.assert_(u'OK' in result)

    def test_list_genre_without_quotes_and_capitalized(self):
        result = self.h.handle_request(u'list Genre')
        self.assert_(u'OK' in result)

    def test_list_genre_with_query_of_one_token(self):
        result = self.h.handle_request(u'list "genre" "anartist"')
        self.assertEqual(result[0],
            u'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_genre_by_artist(self):
        result = self.h.handle_request(u'list "genre" "artist" "anartist"')
        self.assert_(u'OK' in result)

    def test_list_genre_by_album(self):
        result = self.h.handle_request(u'list "genre" "album" "analbum"')
        self.assert_(u'OK' in result)

    def test_list_genre_by_full_date(self):
        result = self.h.handle_request(u'list "genre" "date" "2001-01-01"')
        self.assert_(u'OK' in result)

    def test_list_genre_by_year(self):
        result = self.h.handle_request(u'list "genre" "date" "2001"')
        self.assert_(u'OK' in result)

    def test_list_genre_by_genre(self):
        result = self.h.handle_request(u'list "genre" "genre" "agenre"')
        self.assert_(u'OK' in result)

    def test_list_genre_by_artist_and_album(self):
        result = self.h.handle_request(
            u'list "genre" "artist" "anartist" "album" "analbum"')
        self.assert_(u'OK' in result)


class MusicDatabaseSearchTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

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

    def test_search_date(self):
        result = self.h.handle_request(u'search "date" "2002-01-01"')
        self.assert_(u'OK' in result)

    def test_search_date_without_quotes(self):
        result = self.h.handle_request(u'search date "2002-01-01"')
        self.assert_(u'OK' in result)

    def test_search_date_with_capital_d_and_incomplete_date(self):
        result = self.h.handle_request(u'search Date "2005"')
        self.assert_(u'OK' in result)

    def test_search_else_should_fail(self):
        result = self.h.handle_request(u'search "sometype" "something"')
        self.assertEqual(result[0], u'ACK [2@0] {search} incorrect arguments')


