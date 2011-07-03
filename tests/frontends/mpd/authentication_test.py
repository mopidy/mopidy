import mock
import unittest

from mopidy import settings
from mopidy.frontends.mpd import MpdSession
from mopidy.frontends.mpd.dispatcher import MpdDispatcher

class AuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.session = mock.Mock(spec=MpdSession)
        self.dispatcher = MpdDispatcher(session=self.session)

    def tearDown(self):
        settings.runtime.clear()

    def test_authentication_with_valid_password_is_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'password "topsecret"')
        self.assertTrue(self.dispatcher.authenticated)
        self.assert_(u'OK' in response)

    def test_authentication_with_invalid_password_is_not_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'password "secret"')
        self.assertFalse(self.dispatcher.authenticated)
        self.assert_(u'ACK [3@0] {password} incorrect password' in response)

    def test_authentication_with_anything_when_password_check_turned_off(self):
        settings.MPD_SERVER_PASSWORD = None
        response = self.dispatcher.handle_request(u'any request at all')
        self.assertTrue(self.dispatcher.authenticated)
        self.assert_('ACK [5@0] {} unknown command "any"' in response)

    def test_anything_when_not_authenticated_should_fail(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'any request at all')
        self.assertFalse(self.dispatcher.authenticated)
        self.assert_(
            u'ACK [4@0] {any} you don\'t have permission for "any"' in response)

    def test_close_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'close')
        self.assertFalse(self.dispatcher.authenticated)
        self.assert_(u'OK' in response)

    def test_commands_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'commands')
        self.assertFalse(self.dispatcher.authenticated)
        self.assert_(u'OK' in response)

    def test_notcommands_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'notcommands')
        self.assertFalse(self.dispatcher.authenticated)
        self.assert_(u'OK' in response)

    def test_ping_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        response = self.dispatcher.handle_request(u'ping')
        self.assertFalse(self.dispatcher.authenticated)
        self.assert_(u'OK' in response)
