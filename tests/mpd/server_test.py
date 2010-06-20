import unittest

from mopidy.mpd.server import MpdSession

class MpdServerTest(unittest.TestCase):
    pass # TODO

class MpdSessionTest(unittest.TestCase):
    def setUp(self):
        self.session = MpdSession(None, None, (None, None), None)

    def test_found_terminator_catches_decode_error(self):
        # Pressing Ctrl+C in a telnet session sends a 0xff byte to the server.
        self.session.input_buffer = ['\xff']
        self.session.found_terminator()
        self.assertEqual(len(self.session.input_buffer), 0)
