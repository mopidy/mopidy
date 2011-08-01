from mopidy import settings

from tests.frontends.mpd import protocol


class ReflectionHandlerTest(protocol.BaseTestCase):
    def test_commands_returns_list_of_all_commands(self):
        self.sendRequest(u'commands')
        # Check if some random commands are included
        self.assertInResponse(u'command: commands')
        self.assertInResponse(u'command: play')
        self.assertInResponse(u'command: status')
        # Check if commands you do not have access to are not present
        self.assertNotInResponse(u'command: kill')
        # Check if the blacklisted commands are not present
        self.assertNotInResponse(u'command: command_list_begin')
        self.assertNotInResponse(u'command: command_list_ok_begin')
        self.assertNotInResponse(u'command: command_list_end')
        self.assertNotInResponse(u'command: idle')
        self.assertNotInResponse(u'command: noidle')
        self.assertNotInResponse(u'command: sticker')
        self.assertInResponse(u'OK')

    def test_commands_show_less_if_auth_required_and_not_authed(self):
        settings.MPD_SERVER_PASSWORD = u'secret'
        self.sendRequest(u'commands')
        # Not requiring auth
        self.assertInResponse(u'command: close')
        self.assertInResponse(u'command: commands')
        self.assertInResponse(u'command: notcommands')
        self.assertInResponse(u'command: password')
        self.assertInResponse(u'command: ping')
        # Requiring auth
        self.assertNotInResponse(u'command: play')
        self.assertNotInResponse(u'command: status')

    def test_decoders(self):
        self.sendRequest(u'decoders')
        self.assertInResponse(u'ACK [0@0] {} Not implemented')

    def test_notcommands_returns_only_kill_and_ok(self):
        response = self.sendRequest(u'notcommands')
        self.assertEqual(2, len(response))
        self.assertInResponse(u'command: kill')
        self.assertInResponse(u'OK')

    def test_notcommands_returns_more_if_auth_required_and_not_authed(self):
        settings.MPD_SERVER_PASSWORD = u'secret'
        self.sendRequest(u'notcommands')
        # Not requiring auth
        self.assertNotInResponse(u'command: close')
        self.assertNotInResponse(u'command: commands')
        self.assertNotInResponse(u'command: notcommands')
        self.assertNotInResponse(u'command: password')
        self.assertNotInResponse(u'command: ping')
        # Requiring auth
        self.assertInResponse(u'command: play')
        self.assertInResponse(u'command: status')

    def test_tagtypes(self):
        self.sendRequest(u'tagtypes')
        self.assertInResponse(u'OK')

    def test_urlhandlers(self):
        self.sendRequest(u'urlhandlers')
        self.assertInResponse(u'OK')
        self.assertInResponse(u'handler: dummy')
