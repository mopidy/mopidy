from mopidy import settings

from tests.frontends.mpd import protocol


class AuthenticationTest(protocol.BaseTestCase):
    def test_authentication_with_valid_password_is_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'password "topsecret"')
        self.assertTrue(self.dispatcher.authenticated)
        self.assertInResponse(u'OK')

    def test_authentication_with_invalid_password_is_not_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'password "secret"')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertEqualResponse(u'ACK [3@0] {password} incorrect password')

    def test_authentication_with_anything_when_password_check_turned_off(self):
        settings.MPD_SERVER_PASSWORD = None

        self.sendRequest(u'any request at all')
        self.assertTrue(self.dispatcher.authenticated)
        self.assertEqualResponse('ACK [5@0] {} unknown command "any"')

    def test_anything_when_not_authenticated_should_fail(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'any request at all')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertEqualResponse(
            u'ACK [4@0] {any} you don\'t have permission for "any"')

    def test_close_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'close')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse(u'OK')

    def test_commands_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'commands')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse(u'OK')

    def test_notcommands_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'notcommands')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse(u'OK')

    def test_ping_is_allowed_without_authentication(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'

        self.sendRequest(u'ping')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse(u'OK')
