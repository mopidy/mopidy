from mock import patch

from mopidy import settings

from tests.frontends.mpd import protocol


class ConnectionHandlerTest(protocol.BaseTestCase):
    def test_close_closes_the_client_connection(self):
        with patch.object(self.session, 'close') as close_mock:
            response = self.sendRequest(u'close')
            close_mock.assertEqualResponsecalled_once_with()
        self.assertEqualResponse(u'OK')

    def test_empty_request(self):
        self.sendRequest(u'')
        self.assertEqualResponse(u'OK')

        self.sendRequest(u'  ')
        self.assertEqualResponse(u'OK')

    def test_kill(self):
        self.sendRequest(u'kill')
        self.assertEqualResponse(
            u'ACK [4@0] {kill} you don\'t have permission for "kill"')

    def test_valid_password_is_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        self.sendRequest(u'password "topsecret"')
        self.assertEqualResponse(u'OK')

    def test_invalid_password_is_not_accepted(self):
        settings.MPD_SERVER_PASSWORD = u'topsecret'
        self.sendRequest(u'password "secret"')
        self.assertEqualResponse(u'ACK [3@0] {password} incorrect password')

    def test_any_password_is_not_accepted_when_password_check_turned_off(self):
        settings.MPD_SERVER_PASSWORD = None
        self.sendRequest(u'password "secret"')
        self.assertEqualResponse(u'ACK [3@0] {password} incorrect password')

    def test_ping(self):
        self.sendRequest(u'ping')
        self.assertEqualResponse(u'OK')
