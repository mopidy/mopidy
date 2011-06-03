import mock
import unittest

from mopidy import settings
from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.session import MpdSession
from mopidy.mixers.dummy import DummyMixer

class ConnectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.backend = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.session = mock.Mock(spec=MpdSession)
        self.dispatcher = MpdDispatcher(session=self.session)

    def tearDown(self):
        self.backend.stop().get()
        self.mixer.stop().get()
        settings.runtime.clear()

    def test_close_closes_the_client_connection(self):
        result = self.dispatcher.handle_request(u'close')
        self.assert_(self.session.close.called,
            u'Should call close() on MpdSession')
        self.assert_(u'OK' in result)

    def test_empty_request(self):
        result = self.dispatcher.handle_request(u'')
        self.assert_(u'OK' in result)

    def test_kill(self):
        result = self.dispatcher.handle_request(u'kill')
        self.assert_(u'OK' in result)

    def test_valid_password_is_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        result = self.dispatcher.handle_request(u'password "topsecret"')
        self.assert_(u'OK' in result)

    def test_invalid_password_is_not_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        result = self.dispatcher.handle_request(u'password "secret"')
        self.assert_(u'ACK [3@0] {password} incorrect password' in result)

    def test_any_password_is_not_accepted_when_password_check_turned_off(self):
        settings.MPD_SERVER_PASSWORD = None
        result = self.dispatcher.handle_request(u'password "secret"')
        self.assert_(u'ACK [3@0] {password} incorrect password' in result)

    def test_ping(self):
        result = self.dispatcher.handle_request(u'ping')
        self.assert_(u'OK' in result)
