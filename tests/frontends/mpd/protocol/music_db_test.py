from __future__ import unicode_literals

from mopidy.models import Album, Artist, SearchResult, Track

from tests.frontends.mpd import protocol


class MusicDatabaseHandlerTest(protocol.BaseTestCase):
    def test_count(self):
        self.sendRequest('count "artist" "needle"')
        self.assertInResponse('songs: 0')
        self.assertInResponse('playtime: 0')
        self.assertInResponse('OK')

    def test_count_without_quotes(self):
        self.sendRequest('count artist "needle"')
        self.assertInResponse('songs: 0')
        self.assertInResponse('playtime: 0')
        self.assertInResponse('OK')

    def test_count_with_multiple_pairs(self):
        self.sendRequest('count "artist" "foo" "album" "bar"')
        self.assertInResponse('songs: 0')
        self.assertInResponse('playtime: 0')
        self.assertInResponse('OK')

    def test_count_correct_length(self):
        # Count the lone track
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[
                Track(uri='dummy:a', name="foo", date="2001", length=4000),
            ])
        self.sendRequest('count "title" "foo"')
        self.assertInResponse('songs: 1')
        self.assertInResponse('playtime: 4')
        self.assertInResponse('OK')

        # Count multiple tracks
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[
                Track(uri='dummy:b', date="2001", length=50000),
                Track(uri='dummy:c', date="2001", length=600000),
            ])
        self.sendRequest('count "date" "2001"')
        self.assertInResponse('songs: 2')
        self.assertInResponse('playtime: 650')
        self.assertInResponse('OK')

    def test_findadd(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[Track(uri='dummy:a', name='A')])
        self.assertEqual(self.core.tracklist.length.get(), 0)

        self.sendRequest('findadd "title" "A"')

        self.assertEqual(self.core.tracklist.length.get(), 1)
        self.assertEqual(self.core.tracklist.tracks.get()[0].uri, 'dummy:a')
        self.assertInResponse('OK')

    def test_searchadd(self):
        self.backend.library.dummy_search_result = SearchResult(
            tracks=[Track(uri='dummy:a', name='A')])
        self.assertEqual(self.core.tracklist.length.get(), 0)

        self.sendRequest('searchadd "title" "a"')

        self.assertEqual(self.core.tracklist.length.get(), 1)
        self.assertEqual(self.core.tracklist.tracks.get()[0].uri, 'dummy:a')
        self.assertInResponse('OK')

    def test_searchaddpl_appends_to_existing_playlist(self):
        playlist = self.core.playlists.create('my favs').get()
        playlist = playlist.copy(tracks=[
            Track(uri='dummy:x', name='X'),
            Track(uri='dummy:y', name='y'),
        ])
        self.core.playlists.save(playlist)
        self.backend.library.dummy_search_result = SearchResult(
            tracks=[Track(uri='dummy:a', name='A')])
        playlists = self.core.playlists.filter(name='my favs').get()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(len(playlists[0].tracks), 2)

        self.sendRequest('searchaddpl "my favs" "title" "a"')

        playlists = self.core.playlists.filter(name='my favs').get()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(len(playlists[0].tracks), 3)
        self.assertEqual(playlists[0].tracks[0].uri, 'dummy:x')
        self.assertEqual(playlists[0].tracks[1].uri, 'dummy:y')
        self.assertEqual(playlists[0].tracks[2].uri, 'dummy:a')
        self.assertInResponse('OK')

    def test_searchaddpl_creates_missing_playlist(self):
        self.backend.library.dummy_search_result = SearchResult(
            tracks=[Track(uri='dummy:a', name='A')])
        self.assertEqual(
            len(self.core.playlists.filter(name='my favs').get()), 0)

        self.sendRequest('searchaddpl "my favs" "title" "a"')

        playlists = self.core.playlists.filter(name='my favs').get()
        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0].tracks[0].uri, 'dummy:a')
        self.assertInResponse('OK')

    def test_listall_without_uri(self):
        self.sendRequest('listall')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_listall_with_uri(self):
        self.sendRequest('listall "file:///dev/urandom"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_listallinfo_without_uri(self):
        self.sendRequest('listallinfo')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_listallinfo_with_uri(self):
        self.sendRequest('listallinfo "file:///dev/urandom"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_lsinfo_without_path_returns_same_as_listplaylists(self):
        lsinfo_response = self.sendRequest('lsinfo')
        listplaylists_response = self.sendRequest('listplaylists')
        self.assertEqual(lsinfo_response, listplaylists_response)

    def test_lsinfo_with_empty_path_returns_same_as_listplaylists(self):
        lsinfo_response = self.sendRequest('lsinfo ""')
        listplaylists_response = self.sendRequest('listplaylists')
        self.assertEqual(lsinfo_response, listplaylists_response)

    def test_lsinfo_for_root_returns_same_as_listplaylists(self):
        lsinfo_response = self.sendRequest('lsinfo "/"')
        listplaylists_response = self.sendRequest('listplaylists')
        self.assertEqual(lsinfo_response, listplaylists_response)

    def test_update_without_uri(self):
        self.sendRequest('update')
        self.assertInResponse('updating_db: 0')
        self.assertInResponse('OK')

    def test_update_with_uri(self):
        self.sendRequest('update "file:///dev/urandom"')
        self.assertInResponse('updating_db: 0')
        self.assertInResponse('OK')

    def test_rescan_without_uri(self):
        self.sendRequest('rescan')
        self.assertInResponse('updating_db: 0')
        self.assertInResponse('OK')

    def test_rescan_with_uri(self):
        self.sendRequest('rescan "file:///dev/urandom"')
        self.assertInResponse('updating_db: 0')
        self.assertInResponse('OK')


class MusicDatabaseFindTest(protocol.BaseTestCase):
    def test_find_includes_fake_artist_and_album_tracks(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            albums=[Album(uri='dummy:album:a', name='A', date='2001')],
            artists=[Artist(uri='dummy:artist:b', name='B')],
            tracks=[Track(uri='dummy:track:c', name='C')])

        self.sendRequest('find "any" "foo"')

        self.assertInResponse('file: dummy:artist:b')
        self.assertInResponse('Title: Artist: B')

        self.assertInResponse('file: dummy:album:a')
        self.assertInResponse('Title: Album: A')
        self.assertInResponse('Date: 2001')

        self.assertInResponse('file: dummy:track:c')
        self.assertInResponse('Title: C')

        self.assertInResponse('OK')

    def test_find_artist_does_not_include_fake_artist_tracks(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            albums=[Album(uri='dummy:album:a', name='A', date='2001')],
            artists=[Artist(uri='dummy:artist:b', name='B')],
            tracks=[Track(uri='dummy:track:c', name='C')])

        self.sendRequest('find "artist" "foo"')

        self.assertNotInResponse('file: dummy:artist:b')
        self.assertNotInResponse('Title: Artist: B')

        self.assertInResponse('file: dummy:album:a')
        self.assertInResponse('Title: Album: A')
        self.assertInResponse('Date: 2001')

        self.assertInResponse('file: dummy:track:c')
        self.assertInResponse('Title: C')

        self.assertInResponse('OK')

    def test_find_albumartist_does_not_include_fake_artist_tracks(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            albums=[Album(uri='dummy:album:a', name='A', date='2001')],
            artists=[Artist(uri='dummy:artist:b', name='B')],
            tracks=[Track(uri='dummy:track:c', name='C')])

        self.sendRequest('find "albumartist" "foo"')

        self.assertNotInResponse('file: dummy:artist:b')
        self.assertNotInResponse('Title: Artist: B')

        self.assertInResponse('file: dummy:album:a')
        self.assertInResponse('Title: Album: A')
        self.assertInResponse('Date: 2001')

        self.assertInResponse('file: dummy:track:c')
        self.assertInResponse('Title: C')

        self.assertInResponse('OK')

    def test_find_artist_and_album_does_not_include_fake_tracks(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            albums=[Album(uri='dummy:album:a', name='A', date='2001')],
            artists=[Artist(uri='dummy:artist:b', name='B')],
            tracks=[Track(uri='dummy:track:c', name='C')])

        self.sendRequest('find "artist" "foo" "album" "bar"')

        self.assertNotInResponse('file: dummy:artist:b')
        self.assertNotInResponse('Title: Artist: B')

        self.assertNotInResponse('file: dummy:album:a')
        self.assertNotInResponse('Title: Album: A')
        self.assertNotInResponse('Date: 2001')

        self.assertInResponse('file: dummy:track:c')
        self.assertInResponse('Title: C')

        self.assertInResponse('OK')

    def test_find_album(self):
        self.sendRequest('find "album" "what"')
        self.assertInResponse('OK')

    def test_find_album_without_quotes(self):
        self.sendRequest('find album "what"')
        self.assertInResponse('OK')

    def test_find_artist(self):
        self.sendRequest('find "artist" "what"')
        self.assertInResponse('OK')

    def test_find_artist_without_quotes(self):
        self.sendRequest('find artist "what"')
        self.assertInResponse('OK')

    def test_find_albumartist(self):
        self.sendRequest('find "albumartist" "what"')
        self.assertInResponse('OK')

    def test_find_albumartist_without_quotes(self):
        self.sendRequest('find albumartist "what"')
        self.assertInResponse('OK')

    def test_find_filename(self):
        self.sendRequest('find "filename" "afilename"')
        self.assertInResponse('OK')

    def test_find_filename_without_quotes(self):
        self.sendRequest('find filename "afilename"')
        self.assertInResponse('OK')

    def test_find_file(self):
        self.sendRequest('find "file" "afilename"')
        self.assertInResponse('OK')

    def test_find_file_without_quotes(self):
        self.sendRequest('find file "afilename"')
        self.assertInResponse('OK')

    def test_find_title(self):
        self.sendRequest('find "title" "what"')
        self.assertInResponse('OK')

    def test_find_title_without_quotes(self):
        self.sendRequest('find title "what"')
        self.assertInResponse('OK')

    def test_find_track_no(self):
        self.sendRequest('find "track" "10"')
        self.assertInResponse('OK')

    def test_find_track_no_without_quotes(self):
        self.sendRequest('find track "10"')
        self.assertInResponse('OK')

    def test_find_track_no_without_filter_value(self):
        self.sendRequest('find "track" ""')
        self.assertInResponse('OK')

    def test_find_date(self):
        self.sendRequest('find "date" "2002-01-01"')
        self.assertInResponse('OK')

    def test_find_date_without_quotes(self):
        self.sendRequest('find date "2002-01-01"')
        self.assertInResponse('OK')

    def test_find_date_with_capital_d_and_incomplete_date(self):
        self.sendRequest('find Date "2005"')
        self.assertInResponse('OK')

    def test_find_else_should_fail(self):
        self.sendRequest('find "somethingelse" "what"')
        self.assertEqualResponse('ACK [2@0] {find} incorrect arguments')

    def test_find_album_and_artist(self):
        self.sendRequest('find album "album_what" artist "artist_what"')
        self.assertInResponse('OK')

    def test_find_without_filter_value(self):
        self.sendRequest('find "album" ""')
        self.assertInResponse('OK')


class MusicDatabaseListTest(protocol.BaseTestCase):
    def test_list(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[
                Track(uri='dummy:a', name='A', artists=[
                    Artist(name='A Artist')])])

        self.sendRequest('list "artist" "artist" "foo"')

        self.assertInResponse('Artist: A Artist')
        self.assertInResponse('OK')

    def test_list_foo_returns_ack(self):
        self.sendRequest('list "foo"')
        self.assertEqualResponse('ACK [2@0] {list} incorrect arguments')

    ### Artist

    def test_list_artist_with_quotes(self):
        self.sendRequest('list "artist"')
        self.assertInResponse('OK')

    def test_list_artist_without_quotes(self):
        self.sendRequest('list artist')
        self.assertInResponse('OK')

    def test_list_artist_without_quotes_and_capitalized(self):
        self.sendRequest('list Artist')
        self.assertInResponse('OK')

    def test_list_artist_with_query_of_one_token(self):
        self.sendRequest('list "artist" "anartist"')
        self.assertEqualResponse(
            'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_artist_with_unknown_field_in_query_returns_ack(self):
        self.sendRequest('list "artist" "foo" "bar"')
        self.assertEqualResponse('ACK [2@0] {list} not able to parse args')

    def test_list_artist_by_artist(self):
        self.sendRequest('list "artist" "artist" "anartist"')
        self.assertInResponse('OK')

    def test_list_artist_by_album(self):
        self.sendRequest('list "artist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_artist_by_full_date(self):
        self.sendRequest('list "artist" "date" "2001-01-01"')
        self.assertInResponse('OK')

    def test_list_artist_by_year(self):
        self.sendRequest('list "artist" "date" "2001"')
        self.assertInResponse('OK')

    def test_list_artist_by_genre(self):
        self.sendRequest('list "artist" "genre" "agenre"')
        self.assertInResponse('OK')

    def test_list_artist_by_artist_and_album(self):
        self.sendRequest(
            'list "artist" "artist" "anartist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_artist_without_filter_value(self):
        self.sendRequest('list "artist" "artist" ""')
        self.assertInResponse('OK')

    def test_list_artist_should_not_return_artists_without_names(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[Track(artists=[Artist(name='')])])

        self.sendRequest('list "artist"')
        self.assertNotInResponse('Artist: ')
        self.assertInResponse('OK')

    ### Albumartist

    def test_list_albumartist_with_quotes(self):
        self.sendRequest('list "albumartist"')
        self.assertInResponse('OK')

    def test_list_albumartist_without_quotes(self):
        self.sendRequest('list albumartist')
        self.assertInResponse('OK')

    def test_list_albumartist_without_quotes_and_capitalized(self):
        self.sendRequest('list Albumartist')
        self.assertInResponse('OK')

    def test_list_albumartist_with_query_of_one_token(self):
        self.sendRequest('list "albumartist" "anartist"')
        self.assertEqualResponse(
            'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_albumartist_with_unknown_field_in_query_returns_ack(self):
        self.sendRequest('list "albumartist" "foo" "bar"')
        self.assertEqualResponse('ACK [2@0] {list} not able to parse args')

    def test_list_albumartist_by_artist(self):
        self.sendRequest('list "albumartist" "artist" "anartist"')
        self.assertInResponse('OK')

    def test_list_albumartist_by_album(self):
        self.sendRequest('list "albumartist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_albumartist_by_full_date(self):
        self.sendRequest('list "albumartist" "date" "2001-01-01"')
        self.assertInResponse('OK')

    def test_list_albumartist_by_year(self):
        self.sendRequest('list "albumartist" "date" "2001"')
        self.assertInResponse('OK')

    def test_list_albumartist_by_genre(self):
        self.sendRequest('list "albumartist" "genre" "agenre"')
        self.assertInResponse('OK')

    def test_list_albumartist_by_artist_and_album(self):
        self.sendRequest(
            'list "albumartist" "artist" "anartist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_albumartist_without_filter_value(self):
        self.sendRequest('list "albumartist" "artist" ""')
        self.assertInResponse('OK')

    def test_list_albumartist_should_not_return_artists_without_names(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[Track(album=Album(artists=[Artist(name='')]))])

        self.sendRequest('list "albumartist"')
        self.assertNotInResponse('Artist: ')
        self.assertInResponse('OK')

    ### Album

    def test_list_album_with_quotes(self):
        self.sendRequest('list "album"')
        self.assertInResponse('OK')

    def test_list_album_without_quotes(self):
        self.sendRequest('list album')
        self.assertInResponse('OK')

    def test_list_album_without_quotes_and_capitalized(self):
        self.sendRequest('list Album')
        self.assertInResponse('OK')

    def test_list_album_with_artist_name(self):
        self.sendRequest('list "album" "anartist"')
        self.assertInResponse('OK')

    def test_list_album_with_artist_name_without_filter_value(self):
        self.sendRequest('list "album" ""')
        self.assertInResponse('OK')

    def test_list_album_by_artist(self):
        self.sendRequest('list "album" "artist" "anartist"')
        self.assertInResponse('OK')

    def test_list_album_by_album(self):
        self.sendRequest('list "album" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_album_by_albumartist(self):
        self.sendRequest('list "album" "albumartist" "anartist"')
        self.assertInResponse('OK')

    def test_list_album_by_full_date(self):
        self.sendRequest('list "album" "date" "2001-01-01"')
        self.assertInResponse('OK')

    def test_list_album_by_year(self):
        self.sendRequest('list "album" "date" "2001"')
        self.assertInResponse('OK')

    def test_list_album_by_genre(self):
        self.sendRequest('list "album" "genre" "agenre"')
        self.assertInResponse('OK')

    def test_list_album_by_artist_and_album(self):
        self.sendRequest(
            'list "album" "artist" "anartist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_album_without_filter_value(self):
        self.sendRequest('list "album" "artist" ""')
        self.assertInResponse('OK')

    def test_list_album_should_not_return_albums_without_names(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[Track(album=Album(name=''))])

        self.sendRequest('list "album"')
        self.assertNotInResponse('Album: ')
        self.assertInResponse('OK')

    ### Date

    def test_list_date_with_quotes(self):
        self.sendRequest('list "date"')
        self.assertInResponse('OK')

    def test_list_date_without_quotes(self):
        self.sendRequest('list date')
        self.assertInResponse('OK')

    def test_list_date_without_quotes_and_capitalized(self):
        self.sendRequest('list Date')
        self.assertInResponse('OK')

    def test_list_date_with_query_of_one_token(self):
        self.sendRequest('list "date" "anartist"')
        self.assertEqualResponse(
            'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_date_by_artist(self):
        self.sendRequest('list "date" "artist" "anartist"')
        self.assertInResponse('OK')

    def test_list_date_by_album(self):
        self.sendRequest('list "date" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_date_by_full_date(self):
        self.sendRequest('list "date" "date" "2001-01-01"')
        self.assertInResponse('OK')

    def test_list_date_by_year(self):
        self.sendRequest('list "date" "date" "2001"')
        self.assertInResponse('OK')

    def test_list_date_by_genre(self):
        self.sendRequest('list "date" "genre" "agenre"')
        self.assertInResponse('OK')

    def test_list_date_by_artist_and_album(self):
        self.sendRequest('list "date" "artist" "anartist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_date_without_filter_value(self):
        self.sendRequest('list "date" "artist" ""')
        self.assertInResponse('OK')

    def test_list_date_should_not_return_blank_dates(self):
        self.backend.library.dummy_find_exact_result = SearchResult(
            tracks=[Track(date='')])

        self.sendRequest('list "date"')
        self.assertNotInResponse('Date: ')
        self.assertInResponse('OK')

    ### Genre

    def test_list_genre_with_quotes(self):
        self.sendRequest('list "genre"')
        self.assertInResponse('OK')

    def test_list_genre_without_quotes(self):
        self.sendRequest('list genre')
        self.assertInResponse('OK')

    def test_list_genre_without_quotes_and_capitalized(self):
        self.sendRequest('list Genre')
        self.assertInResponse('OK')

    def test_list_genre_with_query_of_one_token(self):
        self.sendRequest('list "genre" "anartist"')
        self.assertEqualResponse(
            'ACK [2@0] {list} should be "Album" for 3 arguments')

    def test_list_genre_by_artist(self):
        self.sendRequest('list "genre" "artist" "anartist"')
        self.assertInResponse('OK')

    def test_list_genre_by_album(self):
        self.sendRequest('list "genre" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_genre_by_full_date(self):
        self.sendRequest('list "genre" "date" "2001-01-01"')
        self.assertInResponse('OK')

    def test_list_genre_by_year(self):
        self.sendRequest('list "genre" "date" "2001"')
        self.assertInResponse('OK')

    def test_list_genre_by_genre(self):
        self.sendRequest('list "genre" "genre" "agenre"')
        self.assertInResponse('OK')

    def test_list_genre_by_artist_and_album(self):
        self.sendRequest(
            'list "genre" "artist" "anartist" "album" "analbum"')
        self.assertInResponse('OK')

    def test_list_genre_without_filter_value(self):
        self.sendRequest('list "genre" "artist" ""')
        self.assertInResponse('OK')


class MusicDatabaseSearchTest(protocol.BaseTestCase):
    def test_search(self):
        self.backend.library.dummy_search_result = SearchResult(
            albums=[Album(uri='dummy:album:a', name='A')],
            artists=[Artist(uri='dummy:artist:b', name='B')],
            tracks=[Track(uri='dummy:track:c', name='C')])

        self.sendRequest('search "any" "foo"')

        self.assertInResponse('file: dummy:album:a')
        self.assertInResponse('Title: Album: A')
        self.assertInResponse('file: dummy:artist:b')
        self.assertInResponse('Title: Artist: B')
        self.assertInResponse('file: dummy:track:c')
        self.assertInResponse('Title: C')

        self.assertInResponse('OK')

    def test_search_album(self):
        self.sendRequest('search "album" "analbum"')
        self.assertInResponse('OK')

    def test_search_album_without_quotes(self):
        self.sendRequest('search album "analbum"')
        self.assertInResponse('OK')

    def test_search_album_without_filter_value(self):
        self.sendRequest('search "album" ""')
        self.assertInResponse('OK')

    def test_search_artist(self):
        self.sendRequest('search "artist" "anartist"')
        self.assertInResponse('OK')

    def test_search_artist_without_quotes(self):
        self.sendRequest('search artist "anartist"')
        self.assertInResponse('OK')

    def test_search_artist_without_filter_value(self):
        self.sendRequest('search "artist" ""')
        self.assertInResponse('OK')

    def test_search_albumartist(self):
        self.sendRequest('search "albumartist" "analbumartist"')
        self.assertInResponse('OK')

    def test_search_albumartist_without_quotes(self):
        self.sendRequest('search albumartist "analbumartist"')
        self.assertInResponse('OK')

    def test_search_albumartist_without_filter_value(self):
        self.sendRequest('search "albumartist" ""')
        self.assertInResponse('OK')

    def test_search_filename(self):
        self.sendRequest('search "filename" "afilename"')
        self.assertInResponse('OK')

    def test_search_filename_without_quotes(self):
        self.sendRequest('search filename "afilename"')
        self.assertInResponse('OK')

    def test_search_filename_without_filter_value(self):
        self.sendRequest('search "filename" ""')
        self.assertInResponse('OK')

    def test_search_file(self):
        self.sendRequest('search "file" "afilename"')
        self.assertInResponse('OK')

    def test_search_file_without_quotes(self):
        self.sendRequest('search file "afilename"')
        self.assertInResponse('OK')

    def test_search_file_without_filter_value(self):
        self.sendRequest('search "file" ""')
        self.assertInResponse('OK')

    def test_search_title(self):
        self.sendRequest('search "title" "atitle"')
        self.assertInResponse('OK')

    def test_search_title_without_quotes(self):
        self.sendRequest('search title "atitle"')
        self.assertInResponse('OK')

    def test_search_title_without_filter_value(self):
        self.sendRequest('search "title" ""')
        self.assertInResponse('OK')

    def test_search_any(self):
        self.sendRequest('search "any" "anything"')
        self.assertInResponse('OK')

    def test_search_any_without_quotes(self):
        self.sendRequest('search any "anything"')
        self.assertInResponse('OK')

    def test_search_any_without_filter_value(self):
        self.sendRequest('search "any" ""')
        self.assertInResponse('OK')

    def test_search_track_no(self):
        self.sendRequest('search "track" "10"')
        self.assertInResponse('OK')

    def test_search_track_no_without_quotes(self):
        self.sendRequest('search track "10"')
        self.assertInResponse('OK')

    def test_search_track_no_without_filter_value(self):
        self.sendRequest('search "track" ""')
        self.assertInResponse('OK')

    def test_search_date(self):
        self.sendRequest('search "date" "2002-01-01"')
        self.assertInResponse('OK')

    def test_search_date_without_quotes(self):
        self.sendRequest('search date "2002-01-01"')
        self.assertInResponse('OK')

    def test_search_date_with_capital_d_and_incomplete_date(self):
        self.sendRequest('search Date "2005"')
        self.assertInResponse('OK')

    def test_search_date_without_filter_value(self):
        self.sendRequest('search "date" ""')
        self.assertInResponse('OK')

    def test_search_else_should_fail(self):
        self.sendRequest('search "sometype" "something"')
        self.assertEqualResponse('ACK [2@0] {search} incorrect arguments')
