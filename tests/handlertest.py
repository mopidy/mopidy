import unittest

from mopidy import handler

class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.h = handler.MpdHandler()

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
        self.assert_(result is None)

    def test_handling_known_request(self):
        expected = 'magic'
        handler._request_handlers['known request'] = lambda x: expected
        result = self.h.handle_request('known request')
        self.assertEquals(expected, result)

    def test_currentsong(self):
        result = self.h._currentsong()
        self.assert_(result is None)

    def test_listplaylists(self):
        result = self.h._listplaylists()
        self.assert_(result is None)

    def test_lsinfo_for_root_returns_same_as_listplaylists(self):
        lsinfo_result = self.h._lsinfo('/')
        listplaylists_result = self.h._listplaylists()
        self.assertEquals(lsinfo_result, listplaylists_result)

    def test_lsinfo(self):
        result = self.h._lsinfo('')
        self.assert_(result is None)

    def test_ping(self):
        result = self.h._ping()
        self.assert_(result is None)

    def test_version(self):
        result = self.h._plchanges('0')
        self.assert_(result is None)

    def test_status(self):
        result = self.h._status()
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
