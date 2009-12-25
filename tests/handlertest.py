import unittest

from mopidy import handler
from mopidy.backends.dummy import DummyBackend

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

    def test_handling_unknown_request_returns_none(self):
        result = self.h.handle_request('an unhandled request')
        self.assertFalse(result)

    def test_handling_known_request(self):
        expected = 'magic'
        handler._request_handlers['known request'] = lambda x: expected
        result = self.h.handle_request('known request')
        self.assertEquals(expected, result)


class StatusHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_clearerror(self):
        result = self.h.handle_request(u'clearerror')
        self.assert_(result is None)

    def test_currentsong(self):
        result = self.h.handle_request(u'currentsong')
        self.assert_(result is None)

    def test_idle_without_subsystems(self):
        result = self.h.handle_request(u'idle')
        self.assert_(result is None)

    def test_idle_with_subsystems(self):
        result = self.h.handle_request(u'idle database playlist')
        self.assert_(result is None)

    def test_stats(self):
        result = self.h.handle_request(u'stats')
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

    def test_status(self):
        result = self.h.handle_request(u'status')
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
        self.assert_(result is None)

    def test_consume_on(self):
        result = self.h.handle_request(u'consume "1"')
        self.assert_(result is None)

    def test_crossfade(self):
        result = self.h.handle_request(u'crossfade "10"')
        self.assert_(result is None)

    def test_random_off(self):
        result = self.h.handle_request(u'random "0"')
        self.assert_(result is None)

    def test_random_on(self):
        result = self.h.handle_request(u'random "1"')
        self.assert_(result is None)

    def test_repeat_off(self):
        result = self.h.handle_request(u'repeat "0"')
        self.assert_(result is None)

    def test_repeat_on(self):
        result = self.h.handle_request(u'repeat "1"')
        self.assert_(result is None)

    def test_setvol_below_min(self):
        result = self.h.handle_request(u'setvol "-10"')
        self.assert_(result is None)

    def test_setvol_min(self):
        result = self.h.handle_request(u'setvol "0"')
        self.assert_(result is None)

    def test_setvol_middle(self):
        result = self.h.handle_request(u'setvol "50"')
        self.assert_(result is None)

    def test_setvol_max(self):
        result = self.h.handle_request(u'setvol "100"')
        self.assert_(result is None)

    def test_setvol_above_max(self):
        result = self.h.handle_request(u'setvol "110"')
        self.assert_(result is None)

    def test_single_off(self):
        result = self.h.handle_request(u'single "0"')
        self.assert_(result is None)

    def test_single_on(self):
        result = self.h.handle_request(u'single "1"')
        self.assert_(result is None)

    def test_replay_gain_mode_off(self):
        result = self.h.handle_request(u'replay_gain_mode off')
        self.assert_(result is None)

    def test_replay_gain_mode_track(self):
        result = self.h.handle_request(u'replay_gain_mode track')
        self.assert_(result is None)

    def test_replay_gain_mode_album(self):
        result = self.h.handle_request(u'replay_gain_mode album')
        self.assert_(result is None)

    def test_replay_gain_status_default(self):
        expected = u'off'
        result = self.h.handle_request(u'replay_gain_status')
        self.assertEquals(expected, result)

    def test_replay_gain_status_off(self):
        expected = u'off'
        self.h._replay_gain_mode(expected)
        result = self.h.handle_request(u'replay_gain_status')
        self.assertEquals(expected, result)

    #def test_replay_gain_status_track(self):
    #    expected = u'track'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assertEquals(expected, result)

    #def test_replay_gain_status_album(self):
    #    expected = u'album'
    #    self.h._replay_gain_mode(expected)
    #    result = self.h.handle_request(u'replay_gain_status')
    #    self.assertEquals(expected, result)


class PlaybackControlHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_next(self):
        result = self.h.handle_request(u'next')
        self.assert_(result is None)

    def test_pause_off(self):
        result = self.h.handle_request(u'pause 0')
        self.assert_(result is None)

    def test_pause_on(self):
        result = self.h.handle_request(u'pause 1')
        self.assert_(result is None)

    def test_play(self):
        result = self.h.handle_request(u'play "0"')
        self.assert_(result is None)

    def test_playid(self):
        result = self.h.handle_request(u'playid "0"')
        self.assert_(result is None)

    def test_previous(self):
        result = self.h.handle_request(u'previous')
        self.assert_(result is None)

    def test_seek(self):
        result = self.h.handle_request(u'seek 0 30')
        self.assert_(result is None)

    def test_seekid(self):
        result = self.h.handle_request(u'seekid 0 30')
        self.assert_(result is None)

    def test_stop(self):
        result = self.h.handle_request(u'stop')
        self.assert_(result is None)


class CurrentPlaylistHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_add(self):
        result = self.h.handle_request(u'add "file:///dev/urandom"')
        self.assert_(result is None)

    def test_addid_without_songpos(self):
        result = self.h.handle_request(u'addid "file:///dev/urandom"')
        self.assert_('id' in result)

    def test_addid_with_songpos(self):
        result = self.h.handle_request(u'addid "file:///dev/urandom" 0')
        self.assert_('id' in result)

    def test_clear(self):
        result = self.h.handle_request(u'clear')
        self.assert_(result is None)

    def test_delete_songpos(self):
        result = self.h.handle_request(u'delete 5')
        self.assert_(result is None)

    def test_delete_open_range(self):
        result = self.h.handle_request(u'delete 10:')
        self.assert_(result is None)

    def test_delete_closed_range(self):
        result = self.h.handle_request(u'delete 10:20')
        self.assert_(result is None)

    def test_deleteid(self):
        result = self.h.handle_request(u'deleteid 0')
        self.assert_(result is None)

    def test_move_songpos(self):
        result = self.h.handle_request(u'move 5 0')
        self.assert_(result is None)

    def test_move_open_range(self):
        result = self.h.handle_request(u'move 10: 0')
        self.assert_(result is None)

    def test_move_closed_range(self):
        result = self.h.handle_request(u'move 10:20 0')
        self.assert_(result is None)

    def test_moveid(self):
        result = self.h.handle_request(u'moveid 0 10')
        self.assert_(result is None)

    def test_playlist_returns_same_as_playlistinfo(self):
        playlist_result = self.h.handle_request(u'playlist')
        playlistinfo_result = self.h.handle_request(u'playlistinfo')
        self.assertEquals(playlist_result, playlistinfo_result)

    def test_playlistfind(self):
        result = self.h.handle_request(u'playlistfind tag needle')
        self.assert_(result is None)

    def test_playlistid_without_songid(self):
        result = self.h.handle_request(u'playlistid')
        self.assert_(result is None)

    def test_playlistid_with_songid(self):
        result = self.h.handle_request(u'playlistid 10')
        self.assert_(result is None)

    def test_playlistinfo_without_songpos_or_range(self):
        result = self.h.handle_request(u'playlistinfo')
        self.assert_(result is None)

    def test_playlistinfo_with_songpos(self):
        result = self.h.handle_request(u'playlistinfo "5"')
        self.assert_(result is None)

    def test_playlistinfo_with_open_range(self):
        result = self.h.handle_request(u'playlistinfo "10:"')
        self.assert_(result is None)

    def test_playlistinfo_with_closed_range(self):
        result = self.h.handle_request(u'playlistinfo "10:20"')
        self.assert_(result is None)

    def test_playlistsearch(self):
        result = self.h.handle_request(u'playlistsearch tag needle')
        self.assert_(result is None)

    def test_plchanges(self):
        result = self.h.handle_request(u'plchanges "0"')
        self.assert_(result is None)

    def test_plchangesposid(self):
        result = self.h.handle_request(u'plchangesposid 0')
        self.assert_(result is None)

    def test_shuffle_without_range(self):
        result = self.h.handle_request(u'shuffle')
        self.assert_(result is None)

    def test_shuffle_with_open_range(self):
        result = self.h.handle_request(u'shuffle 10:')
        self.assert_(result is None)

    def test_shuffle_with_closed_range(self):
        result = self.h.handle_request(u'shuffle 10:20')
        self.assert_(result is None)

    def test_swap(self):
        result = self.h.handle_request(u'swap 10 20')
        self.assert_(result is None)

    def test_swapid(self):
        result = self.h.handle_request(u'swapid 10 20')
        self.assert_(result is None)


class StoredPlaylistsHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_listplaylist(self):
        result = self.h.handle_request(u'listplaylist name')
        self.assert_(result is None)

    def test_listplaylistinfo(self):
        result = self.h.handle_request(u'listplaylistinfo name')
        self.assert_(result is None)

    def test_listplaylists(self):
        result = self.h.handle_request(u'listplaylists')
        self.assert_(result is None)

    def test_load(self):
        result = self.h.handle_request(u'load "name"')
        self.assert_(result is None)

    def test_playlistadd(self):
        result = self.h.handle_request(
            u'playlistadd name "file:///dev/urandom"')
        self.assert_(result is None)

    def test_playlistclear(self):
        result = self.h.handle_request(u'playlistclear name')
        self.assert_(result is None)

    def test_playlistdelete(self):
        result = self.h.handle_request(u'playlistdelete name 5')
        self.assert_(result is None)

    def test_playlistmove(self):
        result = self.h.handle_request(u'playlistmove name 5a 10')
        self.assert_(result is None)

    def test_rename(self):
        result = self.h.handle_request(u'rename name new_name')
        self.assert_(result is None)

    def test_rm(self):
        result = self.h.handle_request(u'rm name')
        self.assert_(result is None)

    def test_save(self):
        result = self.h.handle_request(u'save name')
        self.assert_(result is None)


class MusicDatabaseHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_count(self):
        result = self.h.handle_request(u'count tag needle')
        self.assert_(result is None)

    def test_find_album(self):
        result = self.h.handle_request(u'find album what')
        self.assert_(result is None)

    def test_find_artist(self):
        result = self.h.handle_request(u'find artist what')
        self.assert_(result is None)

    def test_find_title(self):
        result = self.h.handle_request(u'find title what')
        self.assert_(result is None)

    def test_find_else_should_fail(self):
        result = self.h.handle_request(u'find somethingelse what')
        self.assert_(result is False)

    def test_findadd(self):
        result = self.h.handle_request(u'findadd album what')
        self.assert_(result is None)

    def test_list_artist(self):
        result = self.h.handle_request(u'list artist')
        self.assert_(result is None)

    def test_list_artist_with_artist_should_fail(self):
        result = self.h.handle_request(u'list artist anartist')
        self.assert_(result is False)

    def test_list_album_without_artist(self):
        result = self.h.handle_request(u'list album')
        self.assert_(result is None)

    def test_list_album_with_artist(self):
        result = self.h.handle_request(u'list album anartist')
        self.assert_(result is None)

    def test_listall(self):
        result = self.h.handle_request(u'listall "file:///dev/urandom"')
        self.assert_(result is None)

    def test_listallinfo(self):
        result = self.h.handle_request(u'listallinfo "file:///dev/urandom"')
        self.assert_(result is None)

    def test_lsinfo_without_path_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEquals(lsinfo_result, listplaylists_result)

    def test_lsinfo_with_path(self):
        result = self.h.handle_request(u'lsinfo ""')
        self.assert_(result is None)

    def test_lsinfo_for_root_returns_same_as_listplaylists(self):
        lsinfo_result = self.h.handle_request(u'lsinfo "/"')
        listplaylists_result = self.h.handle_request(u'listplaylists')
        self.assertEquals(lsinfo_result, listplaylists_result)

    def test_search_album(self):
        result = self.h.handle_request(u'search "album" "analbum"')
        self.assert_(result is None)

    def test_search_artist(self):
        result = self.h.handle_request(u'search "artist" "anartist"')
        self.assert_(result is None)

    def test_search_filename(self):
        result = self.h.handle_request(u'search "filename" "afilename"')
        self.assert_(result is None)

    def test_search_title(self):
        result = self.h.handle_request(u'search "title" "atitle"')
        self.assert_(result is None)

    def test_search_else_should_fail(self):
        result = self.h.handle_request(u'search "sometype" "something"')
        self.assert_(result is False)

    def test_update_without_uri(self):
        result = self.h.handle_request(u'update')
        (label, jobid) = result.split(':', 1)
        self.assertEquals(u'updating_db', label)
        self.assert_(jobid.strip().isdigit())
        self.assert_(int(jobid) >= 0)

    def test_update_with_uri(self):
        result = self.h.handle_request(u'update "file:///dev/urandom"')
        (label, jobid) = result.split(':', 1)
        self.assertEquals(u'updating_db', label)
        self.assert_(jobid.strip().isdigit())
        self.assert_(int(jobid) >= 0)

    def test_rescan_without_uri(self):
        result = self.h.handle_request(u'rescan')
        (label, jobid) = result.split(':', 1)
        self.assertEquals(u'updating_db', label)
        self.assert_(jobid.strip().isdigit())
        self.assert_(int(jobid) >= 0)

    def test_rescan_with_uri(self):
        result = self.h.handle_request(u'rescan "file:///dev/urandom"')
        (label, jobid) = result.split(':', 1)
        self.assertEquals(u'updating_db', label)
        self.assert_(jobid.strip().isdigit())
        self.assert_(int(jobid) >= 0)


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
        self.assert_(result is None)

    def test_empty_request(self):
        result = self.h.handle_request(u'')
        self.assert_(result is None)

    def test_kill(self):
        result = self.h.handle_request(u'kill')
        self.assert_(result is None)

    def test_password(self):
        result = self.h.handle_request(u'password "secret"')
        self.assert_(result is None)

    def test_ping(self):
        result = self.h.handle_request(u'ping')
        self.assert_(result is None)

class AudioOutputHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    pass # TODO


class ReflectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler(backend=DummyBackend())

    def test_urlhandlers(self):
        result = self.h.handle_request(u'urlhandlers')
        self.assert_('dummy:' in result)

    pass # TODO
