from __future__ import unicode_literals

from mopidy import settings

from tests.frontends.mpd import protocol


class ReflectionHandlerTest(protocol.BaseTestCase):
    def test_commands_returns_list_of_all_commands(self):
        self.sendRequest('commands')
        # Check if some random commands are included
        self.assertInResponse('command: commands')
        self.assertInResponse('command: play')
        self.assertInResponse('command: status')
        # Check if commands you do not have access to are not present
        self.assertNotInResponse('command: kill')
        # Check if the blacklisted commands are not present
        self.assertNotInResponse('command: command_list_begin')
        self.assertNotInResponse('command: command_list_ok_begin')
        self.assertNotInResponse('command: command_list_end')
        self.assertNotInResponse('command: idle')
        self.assertNotInResponse('command: noidle')
        self.assertNotInResponse('command: sticker')
        self.assertInResponse('OK')

    def test_commands_show_less_if_auth_required_and_not_authed(self):
        settings.MPD_SERVER_PASSWORD = u'secret'
        self.sendRequest('commands')
        # Not requiring auth
        self.assertInResponse('command: close')
        self.assertInResponse('command: commands')
        self.assertInResponse('command: notcommands')
        self.assertInResponse('command: password')
        self.assertInResponse('command: ping')
        # Requiring auth
        self.assertNotInResponse('command: play')
        self.assertNotInResponse('command: status')

    def test_decoders(self):
        self.sendRequest('decoders')
        self.assertInResponse('OK')

    def test_notcommands_returns_only_kill_and_ok(self):
        response = self.sendRequest('notcommands')
        self.assertEqual(2, len(response))
        self.assertInResponse('command: kill')
        self.assertInResponse('OK')

    def test_notcommands_returns_more_if_auth_required_and_not_authed(self):
        settings.MPD_SERVER_PASSWORD = u'secret'
        self.sendRequest('notcommands')
        # Not requiring auth
        self.assertNotInResponse('command: close')
        self.assertNotInResponse('command: commands')
        self.assertNotInResponse('command: notcommands')
        self.assertNotInResponse('command: password')
        self.assertNotInResponse('command: ping')
        # Requiring auth
        self.assertInResponse('command: play')
        self.assertInResponse('command: status')

    def test_tagtypes(self):
        self.sendRequest('tagtypes')
        self.assertInResponse('OK')

    def test_urlhandlers(self):
        self.sendRequest('urlhandlers')
        self.assertInResponse('OK')
        self.assertInResponse('handler: dummy')
