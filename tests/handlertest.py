import unittest

from mopidy import handler
from mopidy.backends.dummy import DummyBackend
from mopidy.exceptions import MpdAckError

class RequestHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_register_same_pattern_twice_fails(self):
        func = lambda: None
        try:
            handler.register('a pattern')(func)
            handler.register('a pattern')(func)
            self.fail('Registering a pattern twice shoulde raise ValueError')
        except ValueError:
            pass

    def test_handling_unknown_request_raises_exception(self):
        try:
            result = self.h.handle_request('an unhandled request')
            self.fail(u'An unknown request should raise an exception')
        except MpdAckError:
            pass

    def test_handling_known_request(self):
        expected = 'magic'
        handler._request_handlers['known request'] = lambda x: expected
        result = self.h.handle_request('known request')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)

class CommandListsTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_command_list_begin(self):
        result = self.h.handle_request(u'command_list_begin')
        self.assert_(result is None)

    def test_command_list_end(self):
        self.h.handle_request(u'command_list_begin')
        result = self.h.handle_request(u'command_list_end')
        self.assert_(u'OK' in result)

    def test_command_list_with_ping(self):
        self.h.handle_request(u'command_list_begin')
        self.assertEquals([], self.h.command_list)
        self.assertEquals(False, self.h.command_list_ok)
        self.h.handle_request(u'ping')
        self.assert_(u'ping' in self.h.command_list)
        result = self.h.handle_request(u'command_list_end')
        self.assert_(u'OK' in result)
        self.assertEquals(False, self.h.command_list)

    def test_command_list_ok_begin(self):
        result = self.h.handle_request(u'command_list_ok_begin')
        self.assert_(result is None)

    def test_command_list_ok_with_ping(self):
        self.h.handle_request(u'command_list_ok_begin')
        self.assertEquals([], self.h.command_list)
        self.assertEquals(True, self.h.command_list_ok)
        self.h.handle_request(u'ping')
        self.assert_(u'ping' in self.h.command_list)
        result = self.h.handle_request(u'command_list_end')
        self.assert_(u'list_OK' in result)
        self.assert_(u'OK' in result)
        self.assertEquals(False, self.h.command_list)
        self.assertEquals(False, self.h.command_list_ok)


class StatusHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_clearerror(self):
        result = self.h.handle_request(u'clearerror')
        self.assert_(u'ACK Not implemented' in result)

    def test_currentsong(self):
        result = self.h.handle_request(u'currentsong')
        self.assert_(u'OK' in result)

    def test_idle_without_subsystems(self):
        result = self.h.handle_request(u'idle')
        self.assert_(u'ACK Not implemented' in result)

    def test_idle_with_subsystems(self):
        result = self.h.handle_request(u'idle database playlist')
        self.assert_(u'ACK Not implemented' in result)

    def test_stats_command(self):
        result = self.h.handle_request(u'stats')
        self.assert_(u'OK' in result)

    def test_stats_method(self):
        result = self.h._stats()
        self.assert_('artists' in result)
        self.assert_(int(result['artists']) >= 0)
        self.assert_('albums' in result)
        self.assert_(int(result['albums']) >= 0)
        self.assert_('songs' in result)
        self.assert_(int(result['songs']) >= 0)
        self.assert_('uptime' in result)
        self.assert_(int(result['uptime']) >= 0)
        self.assert_('db_playtime' in result)
        self.assert_(int(result['db_playtime']) >= 0)
        self.assert_('db_update' in result)
        self.assert_(int(result['db_update']) >= 0)
        self.assert_('playtime' in result)
        self.assert_(int(result['playtime']) >= 0)

    def test_status_command(self):
        result = self.h.handle_request(u'status')
        self.assert_(u'OK' in result)

    def test_status_method(self):
        result = dict(self.h._status())
        self.assert_('volume' in result)
        self.assert_(int(result['volume']) in xrange(0, 101))
        self.assert_('repeat' in result)
        self.assert_(int(result['repeat']) in (0, 1))
        self.assert_('random' in result)
        self.assert_(int(result['random']) in (0, 1))
        self.assert_('single' in result)
        self.assert_(int(result['single']) in (0, 1))
        self.assert_('consume' in result)
        self.assert_(int(result['consume']) in (0, 1))
        self.assert_('playlist' in result)
        self.assert_(int(result['playlist']) in xrange(0, 2**31))
        self.assert_('playlistlength' in result)
        self.assert_(int(result['playlistlength']) >= 0)
        self.assert_('xfade' in result)
        self.assert_(int(result['xfade']) >= 0)
        self.assert_('state' in result)
        self.assert_(result['state'] in ('play', 'stop', 'pause'))


class PlaybackOptionsHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_consume_off(self):
        result = self.h.handle_request(u'consume "0"')
        self.assert_(u'ACK Not implemented' in result)

    def test_consume_on(self):
        result = self.h.handle_request(u'consume "1"')
        self.assert_(u'ACK Not implemented' in result)

    def test_crossfade(self):
        result = self.h.handle_request(u'crossfade "10"')
        self.assert_(u'ACK Not implemented' in result)

    def test_random_off(self):
        result = self.h.handle_request(u'random "0"')
        self.assert_(u'ACK Not implemented' in result)

    def test_random_on(self):
        result = self.h.handle_request(u'random "1"')
        self.assert_(u'ACK Not implemented' in result)

    def test_repeat_off(self):
        result = self.h.handle_request(u'repeat "0"')
        self.assert_(u'ACK Not implemented' in result)

    def test_repeat_on(self):
        result = self.h.handle_request(u'repeat "1"')
        self.assert_(u'ACK Not implemented' in result)

    def test_setvol_below_min(self):
        result = self.h.handle_request(u'setvol "-10"')
        self.assert_(u'ACK Not implemented' in result)

    def test_setvol_min(self):
        result = self.h.handle_request(u'setvol "0"')
        self.assert_(u'ACK Not implemented' in result)

    def test_setvol_middle(self):
        result = self.h.handle_request(u'setvol "50"')
        self.assert_(u'ACK Not implemented' in result)

    def test_setvol_max(self):
        result = self.h.handle_request(u'setvol "100"')
        self.assert_(u'ACK Not implemented' in result)

    def test_setvol_above_max(self):
        result = self.h.handle_request(u'setvol "110"')
        self.assert_(u'ACK Not implemented' in result)

    def test_single_off(self):
        result = self.h.handle_request(u'single "0"')
        self.assert_(u'ACK Not implemented' in result)

    def test_single_on(self):
        result = self.h.handle_request(u'single "1"')
        self.assert_(u'ACK Not implemented' in result)

    def test_replay_gain_mode_off(self):
        result = self.h.handle_request(u'replay_gain_mode off')
        self.assert_(u'ACK Not implemented' in result)

    def test_replay_gain_mode_track(self):
        result = self.h.handle_request(u'replay_gain_mode track')
        self.assert_(u'ACK Not implemented' in result)

    def test_replay_gain_mode_album(self):
        result = self.h.handle_request(u'replay_gain_mode album')
        self.assert_(u'ACK Not implemented' in result)

    def test_replay_gain_status_default(self):
        expected = u'off'
        result = self.h.handle_request(u'replay_gain_status')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)

    #def test_replay_gain_status_off(self):
    #    expected = u'off'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assert_(u'OK' in result)
    #    self.assert_(expected in result)

    #def test_replay_gain_status_track(self):
    #    expected = u'track'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assert_(u'OK' in result)
    #    self.assert_(expected in result)

    #def test_replay_gain_status_album(self):
    #    expected = u'album'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assert_(u'OK' in result)
    #    self.assert_(expected in result)


class PlaybackControlHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend()
        self.h = handler.MpdHandler(backend=self.b)

    def test_next(self):
        result = self.h.handle_request(u'next')
        self.assert_(u'OK' in result)

    def test_pause_off(self):
        result = self.h.handle_request(u'pause "0"')
        self.assert_(u'OK' in result)
        self.assertEquals(self.b.PLAY, self.b.state)

    def test_pause_on(self):
        result = self.h.handle_request(u'pause "1"')
        self.assert_(u'OK' in result)
        self.assertEquals(self.b.PAUSE, self.b.state)

    def test_play(self):
        result = self.h.handle_request(u'play "0"')
        self.assert_(u'OK' in result)
        self.assertEquals(self.b.PLAY, self.b.state)

    def test_playid(self):
        result = self.h.handle_request(u'playid "0"')
        self.assert_(u'OK' in result)
        self.assertEquals(self.b.PLAY, self.b.state)

    def test_previous(self):
        result = self.h.handle_request(u'previous')
        self.assert_(u'OK' in result)

    def test_seek(self):
        result = self.h.handle_request(u'seek 0 30')
        self.assert_(u'ACK Not implemented' in result)

    def test_seekid(self):
        result = self.h.handle_request(u'seekid 0 30')
        self.assert_(u'ACK Not implemented' in result)

    def test_stop(self):
        result = self.h.handle_request(u'stop')
        self.assert_(u'OK' in result)
        self.assertEquals(self.b.STOP, self.b.state)


class CurrentPlaylistHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_add(self):
        result = self.h.handle_request(u'add "file:///dev/urandom"')
        self.assert_(u'ACK Not implemented' in result)

    def test_addid_without_songpos(self):
        result = self.h.handle_request(u'addid "file:///dev/urandom"')
        self.assert_(u'ACK Not implemented' in result)

    def test_addid_with_songpos(self):
        result = self.h.handle_request(u'addid "file:///dev/urandom" 0')
        self.assert_(u'ACK Not implemented' in result)

    def test_clear(self):
        result = self.h.handle_request(u'clear')
        self.assert_(u'ACK Not implemented' in result)

    def test_delete_songpos(self):
        result = self.h.handle_request(u'delete 5')
        self.assert_(u'ACK Not implemented' in result)

    def test_delete_open_range(self):
        result = self.h.handle_request(u'delete 10:')
        self.assert_(u'ACK Not implemented' in result)

    def test_delete_closed_range(self):
        result = self.h.handle_request(u'delete 10:20')
        self.assert_(u'ACK Not implemented' in result)

    def test_deleteid(self):
        result = self.h.handle_request(u'deleteid 0')
        self.assert_(u'ACK Not implemented' in result)

    def test_move_songpos(self):
        result = self.h.handle_request(u'move 5 0')
        self.assert_(u'ACK Not implemented' in result)

    def test_move_open_range(self):
        result = self.h.handle_request(u'move 10: 0')
        self.assert_(u'ACK Not implemented' in result)

    def test_move_closed_range(self):
        result = self.h.handle_request(u'move 10:20 0')
        self.assert_(u'ACK Not implemented' in result)

    def test_moveid(self):
        result = self.h.handle_request(u'moveid 0 10')
        self.assert_(u'ACK Not implemented' in result)

    def test_playlist_returns_same_as_playlistinfo(self):
        playlist_result = self.h.handle_request(u'playlist')
        playlistinfo_result = self.h.handle_request(u'playlistinfo')
        self.assertEquals(playlist_result, playlistinfo_result)

    def test_playlistfind(self):
        result = self.h.handle_request(u'playlistfind tag needle')
        self.assert_(u'ACK Not implemented' in result)

    def test_playlistid_without_songid(self):
        result = self.h.handle_request(u'playlistid')
        self.assert_(u'OK' in result)

    def test_playlistid_with_songid(self):
        result = self.h.handle_request(u'playlistid "10"')
        self.assert_(u'OK' in result)

    def test_playlistinfo_without_songpos_or_range(self):
        result = self.h.handle_request(u'playlistinfo')
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_songpos(self):
        result = self.h.handle_request(u'playlistinfo "5"')
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_open_range(self):
        result = self.h.handle_request(u'playlistinfo "10:"')
        self.assert_(u'OK' in result)

    def test_playlistinfo_with_closed_range(self):
        result = self.h.handle_request(u'playlistinfo "10:20"')
        self.assert_(u'OK' in result)

    def test_playlistsearch(self):
        result = self.h.handle_request(u'playlistsearch tag needle')
        self.assert_(u'ACK Not implemented' in result)

    def test_plchanges(self):
        result = self.h.handle_request(u'plchanges "0"')
        self.assert_(u'OK' in result)

    def test_plchangesposid(self):
        result = self.h.handle_request(u'plchangesposid 0')
        self.assert_(u'ACK Not implemented' in result)

    def test_shuffle_without_range(self):
        result = self.h.handle_request(u'shuffle')
        self.assert_(u'ACK Not implemented' in result)

    def test_shuffle_with_open_range(self):
        result = self.h.handle_request(u'shuffle 10:')
        self.assert_(u'ACK Not implemented' in result)

    def test_shuffle_with_closed_range(self):
        result = self.h.handle_request(u'shuffle 10:20')
        self.assert_(u'ACK Not implemented' in result)

    def test_swap(self):
        result = self.h.handle_request(u'swap 10 20')
        self.assert_(u'ACK Not implemented' in result)

    def test_swapid(self):
        result = self.h.handle_request(u'swapid 10 20')
        self.assert_(u'ACK Not implemented' in result)


class StoredPlaylistsHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_listplaylist(self):
        result = self.h.handle_request(u'listplaylist name')
        self.assert_(u'ACK Not implemented' in result)

    def test_listplaylistinfo(self):
        result = self.h.handle_request(u'listplaylistinfo name')
        self.assert_(u'ACK Not implemented' in result)

    def test_listplaylists(self):
        result = self.h.handle_request(u'listplaylists')
        self.assert_(u'OK' in result)

    def test_load(self):
        result = self.h.handle_request(u'load "name"')
        self.assert_(u'OK' in result)

    def test_playlistadd(self):
        result = self.h.handle_request(
            u'playlistadd name "file:///dev/urandom"')
        self.assert_(u'ACK Not implemented' in result)

    def test_playlistclear(self):
        result = self.h.handle_request(u'playlistclear name')
        self.assert_(u'ACK Not implemented' in result)

    def test_playlistdelete(self):
        result = self.h.handle_request(u'playlistdelete name 5')
        self.assert_(u'ACK Not implemented' in result)

    def test_playlistmove(self):
        result = self.h.handle_request(u'playlistmove name 5a 10')
        self.assert_(u'ACK Not implemented' in result)

    def test_rename(self):
        result = self.h.handle_request(u'rename name new_name')
        self.assert_(u'ACK Not implemented' in result)

    def test_rm(self):
        result = self.h.handle_request(u'rm name')
        self.assert_(u'ACK Not implemented' in result)

    def test_save(self):
        result = self.h.handle_request(u'save name')
        self.assert_(u'ACK Not implemented' in result)


class MusicDatabaseHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_count(self):
        result = self.h.handle_request(u'count tag needle')
        self.assert_(u'ACK Not implemented' in result)

    def test_find_album(self):
        result = self.h.handle_request(u'find album what')
        self.assert_(u'ACK Not implemented' in result)

    def test_find_artist(self):
        result = self.h.handle_request(u'find artist what')
        self.assert_(u'ACK Not implemented' in result)

    def test_find_title(self):
        result = self.h.handle_request(u'find title what')
        self.assert_(u'ACK Not implemented' in result)

    def test_find_else_should_fail(self):
        try:
            result = self.h.handle_request(u'find somethingelse what')
            self.fail('Find with unknown type should fail')
        except MpdAckError:
            pass

    def test_findadd(self):
        result = self.h.handle_request(u'findadd album what')
        self.assert_(u'ACK Not implemented' in result)

    def test_list_artist(self):
        result = self.h.handle_request(u'list artist')
        self.assert_(u'ACK Not implemented' in result)

    def test_list_artist_with_artist_should_fail(self):
        try:
            result = self.h.handle_request(u'list artist anartist')
            self.fail(u'Listing artists filtered by an artist should fail')
        except MpdAckError:
            pass

    def test_list_album_without_artist(self):
        result = self.h.handle_request(u'list album')
        self.assert_(u'ACK Not implemented' in result)

    def test_list_album_with_artist(self):
        result = self.h.handle_request(u'list album anartist')
        self.assert_(u'ACK Not implemented' in result)

    def test_listall(self):
        result = self.h.handle_request(u'listall "file:///dev/urandom"')
        self.assert_(u'ACK Not implemented' in result)

    def test_listallinfo(self):
        result = self.h.handle_request(u'listallinfo "file:///dev/urandom"')
        self.assert_(u'ACK Not implemented' in result)

    def test_lsinfo_without_path_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEquals(lsinfo_result, listplaylists_result)

    def test_lsinfo_with_path(self):
        result = self.h.handle_request(u'lsinfo ""')
        self.assert_(u'ACK Not implemented' in result)

    def test_lsinfo_for_root_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo "/"')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEquals(lsinfo_result, listplaylists_result)

    def test_search_album(self):
        result = self.h.handle_request(u'search "album" "analbum"')
        self.assert_(u'None', result)

    def test_search_artist(self):
        result = self.h.handle_request(u'search "artist" "anartist"')
        self.assert_(u'None', result)

    def test_search_filename(self):
        result = self.h.handle_request(u'search "filename" "afilename"')
        self.assert_(u'None', result)

    def test_search_title(self):
        result = self.h.handle_request(u'search "title" "atitle"')
        self.assert_(u'None', result)

    def test_search_else_should_fail(self):
        try:
            result = self.h.handle_request(u'search "sometype" "something"')
            self.fail(u'Search with unknown type should fail')
        except MpdAckError:
            pass

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


class StickersHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    pass # TODO


class DummySession(object):
    def do_close(self):
        pass

    def do_kill(self):
        pass


class ConnectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(session=DummySession(),
            backend=DummyBackend())

    def test_close(self):
        result = self.h.handle_request(u'close')
        self.assert_(u'OK' in result)

    def test_empty_request(self):
        result = self.h.handle_request(u'')
        self.assert_(u'OK' in result)

    def test_kill(self):
        result = self.h.handle_request(u'kill')
        self.assert_(u'OK' in result)

    def test_password(self):
        result = self.h.handle_request(u'password "secret"')
        self.assert_(u'ACK Not implemented' in result)

    def test_ping(self):
        result = self.h.handle_request(u'ping')
        self.assert_(u'OK' in result)

class AudioOutputHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    pass # TODO


class ReflectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_urlhandlers(self):
        result = self.h.handle_request(u'urlhandlers')
        self.assert_(u'OK' in result)
        result = result[0]
        self.assert_('dummy:' in result)

    pass # TODO
