from tests.frontends.mpd import protocol


class MusicDatabaseHandlerTest(protocol.BaseTestCase):
    def test_count(self):
        self.sendRequest(u'count "tag" "needle"')
        self.assertInResponse(u'songs: 0')
        self.assertInResponse(u'playtime: 0')
        self.assertInResponse(u'OK')

    def test_findadd(self):
        self.sendRequest(u'findadd "album" "what"')
        self.assertInResponse(u'OK')

    def test_listall(self):
        self.sendRequest(u'listall "file:///dev/urandom"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_listallinfo(self):
        self.sendRequest(u'listallinfo "file:///dev/urandom"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_lsinfo_without_path_returns_same_as_listplaylists(self):
        lsinfo_response = self.sendRequest(u'lsinfo')
        listplaylists_response = self.sendRequest(u'listplaylists')
        self.assertEqual(lsinfo_response, listplaylists_response)

    def test_lsinfo_with_empty_path_returns_same_as_listplaylists(self):
        lsinfo_response = self.sendRequest(u'lsinfo ""')
        listplaylists_response = self.sendRequest(u'listplaylists')
        self.assertEqual(lsinfo_response, listplaylists_response)

    def test_lsinfo_for_root_returns_same_as_listplaylists(self):
        lsinfo_response = self.sendRequest(u'lsinfo "/"')
        listplaylists_response = self.sendRequest(u'listplaylists')
        self.assertEqual(lsinfo_response, listplaylists_response)

    def test_update_without_uri(self):
        self.sendRequest(u'update')
        self.assertInResponse(u'updating_db: 0')
        self.assertInResponse(u'OK')

    def test_update_with_uri(self):
        self.sendRequest(u'update "file:///dev/urandom"')
        self.assertInResponse(u'updating_db: 0')
        self.assertInResponse(u'OK')

    def test_rescan_without_uri(self):
        self.sendRequest(u'rescan')
        self.assertInResponse(u'updating_db: 0')
        self.assertInResponse(u'OK')

    def test_rescan_with_uri(self):
        self.sendRequest(u'rescan "file:///dev/urandom"')
        self.assertInResponse(u'updating_db: 0')
        self.assertInResponse(u'OK')


class MusicDatabaseFindTest(protocol.BaseTestCase):
    def test_find_album(self):
        self.sendRequest(u'find "album" "what"')
        self.assertInResponse(u'OK')

    def test_find_album_without_quotes(self):
        self.sendRequest(u'find album "what"')
        self.assertInResponse(u'OK')

    def test_find_artist(self):
        self.sendRequest(u'find "artist" "what"')
        self.assertInResponse(u'OK')

    def test_find_artist_without_quotes(self):
        self.sendRequest(u'find artist "what"')
        self.assertInResponse(u'OK')

    def test_find_title(self):
        self.sendRequest(u'find "title" "what"')
        self.assertInResponse(u'OK')

    def test_find_title_without_quotes(self):
        self.sendRequest(u'find title "what"')
        self.assertInResponse(u'OK')

    def test_find_date(self):
        self.sendRequest(u'find "date" "2002-01-01"')
        self.assertInResponse(u'OK')

    def test_find_date_without_quotes(self):
        self.sendRequest(u'find date "2002-01-01"')
        self.assertInResponse(u'OK')

    def test_find_date_with_capital_d_and_incomplete_date(self):
        self.sendRequest(u'find Date "2005"')
        self.assertInResponse(u'OK')

    def test_find_else_should_fail(self):
        self.sendRequest(u'find "somethingelse" "what"')
        self.assertEqualResponse(u'ACK [2@0] {find} incorrect arguments')

    def test_find_album_and_artist(self):
        self.sendRequest(u'find album "album_what" artist "artist_what"')
        self.assertInResponse(u'OK')


class MusicDatabaseListTest(protocol.BaseTestCase):
    def test_list_foo_returns_ack(self):
        self.sendRequest(u'list "foo"')
        self.assertEqualResponse(u'ACK [2@0] {list} incorrect arguments')

    ### Artist

    def test_list_artist_with_quotes(self):
        self.sendRequest(u'list "artist"')
        self.assertInResponse(u'OK')

    def test_list_artist_without_quotes(self):
        self.sendRequest(u'list artist')
        self.assertInResponse(u'OK')

    def test_list_artist_without_quotes_and_capitalized(self):
        self.sendRequest(u'list Artist')
        self.assertInResponse(u'OK')

    def test_list_artist_with_query_of_one_token(self):
        self.sendRequest(u'list "artist" "anartist"')
        self.assertEqualResponse(
            u'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_artist_with_unknown_field_in_query_returns_ack(self):
        self.sendRequest(u'list "artist" "foo" "bar"')
        self.assertEqualResponse(u'ACK [2@0] {list} not able to parse args')

    def test_list_artist_by_artist(self):
        self.sendRequest(u'list "artist" "artist" "anartist"')
        self.assertInResponse(u'OK')

    def test_list_artist_by_album(self):
        self.sendRequest(u'list "artist" "album" "analbum"')
        self.assertInResponse(u'OK')

    def test_list_artist_by_full_date(self):
        self.sendRequest(u'list "artist" "date" "2001-01-01"')
        self.assertInResponse(u'OK')

    def test_list_artist_by_year(self):
        self.sendRequest(u'list "artist" "date" "2001"')
        self.assertInResponse(u'OK')

    def test_list_artist_by_genre(self):
        self.sendRequest(u'list "artist" "genre" "agenre"')
        self.assertInResponse(u'OK')

    def test_list_artist_by_artist_and_album(self):
        self.sendRequest(
            u'list "artist" "artist" "anartist" "album" "analbum"')
        self.assertInResponse(u'OK')

    ### Album

    def test_list_album_with_quotes(self):
        self.sendRequest(u'list "album"')
        self.assertInResponse(u'OK')

    def test_list_album_without_quotes(self):
        self.sendRequest(u'list album')
        self.assertInResponse(u'OK')

    def test_list_album_without_quotes_and_capitalized(self):
        self.sendRequest(u'list Album')
        self.assertInResponse(u'OK')

    def test_list_album_with_artist_name(self):
        self.sendRequest(u'list "album" "anartist"')
        self.assertInResponse(u'OK')

    def test_list_album_by_artist(self):
        self.sendRequest(u'list "album" "artist" "anartist"')
        self.assertInResponse(u'OK')

    def test_list_album_by_album(self):
        self.sendRequest(u'list "album" "album" "analbum"')
        self.assertInResponse(u'OK')

    def test_list_album_by_full_date(self):
        self.sendRequest(u'list "album" "date" "2001-01-01"')
        self.assertInResponse(u'OK')

    def test_list_album_by_year(self):
        self.sendRequest(u'list "album" "date" "2001"')
        self.assertInResponse(u'OK')

    def test_list_album_by_genre(self):
        self.sendRequest(u'list "album" "genre" "agenre"')
        self.assertInResponse(u'OK')

    def test_list_album_by_artist_and_album(self):
        self.sendRequest(
            u'list "album" "artist" "anartist" "album" "analbum"')
        self.assertInResponse(u'OK')

    ### Date

    def test_list_date_with_quotes(self):
        self.sendRequest(u'list "date"')
        self.assertInResponse(u'OK')

    def test_list_date_without_quotes(self):
        self.sendRequest(u'list date')
        self.assertInResponse(u'OK')

    def test_list_date_without_quotes_and_capitalized(self):
        self.sendRequest(u'list Date')
        self.assertInResponse(u'OK')

    def test_list_date_with_query_of_one_token(self):
        self.sendRequest(u'list "date" "anartist"')
        self.assertEqualResponse(
            u'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_date_by_artist(self):
        self.sendRequest(u'list "date" "artist" "anartist"')
        self.assertInResponse(u'OK')

    def test_list_date_by_album(self):
        self.sendRequest(u'list "date" "album" "analbum"')
        self.assertInResponse(u'OK')

    def test_list_date_by_full_date(self):
        self.sendRequest(u'list "date" "date" "2001-01-01"')
        self.assertInResponse(u'OK')

    def test_list_date_by_year(self):
        self.sendRequest(u'list "date" "date" "2001"')
        self.assertInResponse(u'OK')

    def test_list_date_by_genre(self):
        self.sendRequest(u'list "date" "genre" "agenre"')
        self.assertInResponse(u'OK')

    def test_list_date_by_artist_and_album(self):
        self.sendRequest(u'list "date" "artist" "anartist" "album" "analbum"')
        self.assertInResponse(u'OK')

    ### Genre

    def test_list_genre_with_quotes(self):
        self.sendRequest(u'list "genre"')
        self.assertInResponse(u'OK')

    def test_list_genre_without_quotes(self):
        self.sendRequest(u'list genre')
        self.assertInResponse(u'OK')

    def test_list_genre_without_quotes_and_capitalized(self):
        self.sendRequest(u'list Genre')
        self.assertInResponse(u'OK')

    def test_list_genre_with_query_of_one_token(self):
        self.sendRequest(u'list "genre" "anartist"')
        self.assertEqualResponse(
            u'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_genre_by_artist(self):
        self.sendRequest(u'list "genre" "artist" "anartist"')
        self.assertInResponse(u'OK')

    def test_list_genre_by_album(self):
        self.sendRequest(u'list "genre" "album" "analbum"')
        self.assertInResponse(u'OK')

    def test_list_genre_by_full_date(self):
        self.sendRequest(u'list "genre" "date" "2001-01-01"')
        self.assertInResponse(u'OK')

    def test_list_genre_by_year(self):
        self.sendRequest(u'list "genre" "date" "2001"')
        self.assertInResponse(u'OK')

    def test_list_genre_by_genre(self):
        self.sendRequest(u'list "genre" "genre" "agenre"')
        self.assertInResponse(u'OK')

    def test_list_genre_by_artist_and_album(self):
        self.sendRequest(
            u'list "genre" "artist" "anartist" "album" "analbum"')
        self.assertInResponse(u'OK')


class MusicDatabaseSearchTest(protocol.BaseTestCase):
    def test_search_album(self):
        self.sendRequest(u'search "album" "analbum"')
        self.assertInResponse(u'OK')

    def test_search_album_without_quotes(self):
        self.sendRequest(u'search album "analbum"')
        self.assertInResponse(u'OK')

    def test_search_artist(self):
        self.sendRequest(u'search "artist" "anartist"')
        self.assertInResponse(u'OK')

    def test_search_artist_without_quotes(self):
        self.sendRequest(u'search artist "anartist"')
        self.assertInResponse(u'OK')

    def test_search_filename(self):
        self.sendRequest(u'search "filename" "afilename"')
        self.assertInResponse(u'OK')

    def test_search_filename_without_quotes(self):
        self.sendRequest(u'search filename "afilename"')
        self.assertInResponse(u'OK')

    def test_search_title(self):
        self.sendRequest(u'search "title" "atitle"')
        self.assertInResponse(u'OK')

    def test_search_title_without_quotes(self):
        self.sendRequest(u'search title "atitle"')
        self.assertInResponse(u'OK')

    def test_search_any(self):
        self.sendRequest(u'search "any" "anything"')
        self.assertInResponse(u'OK')

    def test_search_any_without_quotes(self):
        self.sendRequest(u'search any "anything"')
        self.assertInResponse(u'OK')

    def test_search_date(self):
        self.sendRequest(u'search "date" "2002-01-01"')
        self.assertInResponse(u'OK')

    def test_search_date_without_quotes(self):
        self.sendRequest(u'search date "2002-01-01"')
        self.assertInResponse(u'OK')

    def test_search_date_with_capital_d_and_incomplete_date(self):
        self.sendRequest(u'search Date "2005"')
        self.assertInResponse(u'OK')

    def test_search_else_should_fail(self):
        self.sendRequest(u'search "sometype" "something"')
        self.assertEqualResponse(u'ACK [2@0] {search} incorrect arguments')
