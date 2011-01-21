import unittest

from mopidy import settings
from mopidy.frontends.mpd import server

class MpdServerTest(unittest.TestCase):
    def setUp(self):
        self.server = server.MpdServer(None)

    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        server.socket.has_ipv6 = True
        self.assertEqual(self.server._format_hostname('0.0.0.0'),
            '::ffff:0.0.0.0')
        self.assertEqual(self.server._format_hostname('127.0.0.1'),
            '::ffff:127.0.0.1')

    def test_format_hostname_does_nothing_when_only_ipv4_available(self):
        server.socket.has_ipv6 = False
        self.assertEquals(self.server._format_hostname('0.0.0.0'), '0.0.0.0')

class MpdSessionTest(unittest.TestCase):
    def setUp(self):
        self.session = server.MpdSession(None, None, (None, None), None)

    def tearDown(self):
        settings.runtime.clear()

    def test_found_terminator_catches_decode_error(self):
        # Pressing Ctrl+C in a telnet session sends a 0xff byte to the server.
        self.session.input_buffer = ['\xff']
        self.session.found_terminator()
        self.assertEqual(len(self.session.input_buffer), 0)

    def test_authentication_with_valid_password_is_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'password "topsecret"')
        self.assertTrue(authed)
        self.assertEqual(u'OK', response)

    def test_authentication_with_invalid_password_is_not_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'password "secret"')
        self.assertFalse(authed)
        self.assertEqual(u'ACK [3@0] {password} incorrect password', response)

    def test_authentication_with_anything_when_password_check_turned_off(self):
        settings.MPD_SERVER_PASSWORD = False
        authed, response = self.session.check_password(u'any request at all')
        self.assertTrue(authed)
        self.assertEqual(None, response)

    def test_anything_when_not_authenticated_should_fail(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'any request at all')
        self.assertFalse(authed)
        self.assertEqual(
            u'ACK [4@0] {any} you don\'t have permission for "any"', response)

    def test_close_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'close')
        self.assertFalse(authed)
        self.assertEqual(None, response)

    def test_commands_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'commands')
        self.assertFalse(authed)
        self.assertEqual(None, response)

    def test_notcommands_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'notcommands')
        self.assertFalse(authed)
        self.assertEqual(None, response)

    def test_ping_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        authed, response = self.session.check_password(u'ping')
        self.assertFalse(authed)
        self.assertEqual(None, response)
