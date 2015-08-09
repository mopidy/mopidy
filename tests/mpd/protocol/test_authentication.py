from __future__ import absolute_import, unicode_literals

from tests.mpd import protocol


class AuthenticationActiveTest(protocol.BaseTestCase):

    def get_config(self):
        config = super(AuthenticationActiveTest, self).get_config()
        config['mpd']['password'] = 'topsecret'
        return config

    def test_authentication_with_valid_password_is_accepted(self):
        self.send_request('password "topsecret"')
        self.assertTrue(self.dispatcher.authenticated)
        self.assertInResponse('OK')

    def test_authentication_with_invalid_password_is_not_accepted(self):
        self.send_request('password "secret"')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertEqualResponse('ACK [3@0] {password} incorrect password')

    def test_authentication_without_password_fails(self):
        self.send_request('password')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertEqualResponse(
            'ACK [2@0] {password} wrong number of arguments for "password"')

    def test_anything_when_not_authenticated_should_fail(self):
        self.send_request('any request at all')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertEqualResponse(
            u'ACK [4@0] {any} you don\'t have permission for "any"')

    def test_close_is_allowed_without_authentication(self):
        self.send_request('close')
        self.assertFalse(self.dispatcher.authenticated)

    def test_commands_is_allowed_without_authentication(self):
        self.send_request('commands')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse('OK')

    def test_notcommands_is_allowed_without_authentication(self):
        self.send_request('notcommands')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse('OK')

    def test_ping_is_allowed_without_authentication(self):
        self.send_request('ping')
        self.assertFalse(self.dispatcher.authenticated)
        self.assertInResponse('OK')


class AuthenticationInactiveTest(protocol.BaseTestCase):

    def test_authentication_with_anything_when_password_check_turned_off(self):
        self.send_request('any request at all')
        self.assertTrue(self.dispatcher.authenticated)
        self.assertEqualResponse('ACK [5@0] {} unknown command "any"')

    def test_any_password_is_not_accepted_when_password_check_turned_off(self):
        self.send_request('password "secret"')
        self.assertEqualResponse('ACK [3@0] {password} incorrect password')
