import unittest

from mopidy.mpd.server import MpdServer, MpdSession

class MpdServerTest(unittest.TestCase):
    def setUp(self):
        self.server = MpdServer(None)

    def test_format_hostname_prefixes_ipv4_addresses(self):
        self.assertEqual(self.server._format_hostname('0.0.0.0'),
            '::ffff:0.0.0.0')
        self.assertEqual(self.server._format_hostname('127.0.0.1'),
            '::ffff:127.0.0.1')

class MpdSessionTest(unittest.TestCase):
    def setUp(self):
        self.session = MpdSession(None, None, (None, None), None)

    def test_found_terminator_catches_decode_error(self):
        # Pressing Ctrl+C in a telnet session sends a 0xff byte to the server.
        self.session.input_buffer = ['\xff']
        self.session.found_terminator()
        self.assertEqual(len(self.session.input_buffer), 0)
