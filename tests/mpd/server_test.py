import unittest

from mopidy.mpd import server

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

    def test_found_terminator_catches_decode_error(self):
        # Pressing Ctrl+C in a telnet session sends a 0xff byte to the server.
        self.session.input_buffer = ['\xff']
        self.session.found_terminator()
        self.assertEqual(len(self.session.input_buffer), 0)
