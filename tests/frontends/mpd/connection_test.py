import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher

class ConnectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend()
        self.h = dispatcher.MpdDispatcher(backend=self.b)

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
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_ping(self):
        result = self.h.handle_request(u'ping')
        self.assert_(u'OK' in result)
