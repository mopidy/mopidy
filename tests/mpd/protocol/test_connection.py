from __future__ import unicode_literals

from mock import patch

from tests.mpd import protocol


class ConnectionHandlerTest(protocol.BaseTestCase):
    def test_close_closes_the_client_connection(self):
        with patch.object(self.session, 'close') as close_mock:
            self.sendRequest('close')
            close_mock.assertEqualResponsecalled_once_with()
        self.assertEqualResponse('OK')

    def test_empty_request(self):
        self.sendRequest('')
        self.assertEqualResponse('ACK [5@0] {} No command given')

        self.sendRequest('  ')
        self.assertEqualResponse('ACK [5@0] {} No command given')

    def test_kill(self):
        self.sendRequest('kill')
        self.assertEqualResponse(
            'ACK [4@0] {kill} you don\'t have permission for "kill"')

    def test_ping(self):
        self.sendRequest('ping')
        self.assertEqualResponse('OK')
