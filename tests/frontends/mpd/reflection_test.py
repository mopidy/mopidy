import unittest

from mopidy import settings
from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.mixers.dummy import DummyMixer

class ReflectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.backend = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.dispatcher = MpdDispatcher()

    def tearDown(self):
        settings.runtime.clear()
        self.backend.stop().get()
        self.mixer.stop().get()

    def test_commands_returns_list_of_all_commands(self):
        result = self.dispatcher.handle_request(u'commands')
        # Check if some random commands are included
        self.assert_(u'command: commands' in result)
        self.assert_(u'command: play' in result)
        self.assert_(u'command: status' in result)
        # Check if commands you do not have access to are not present
        self.assert_(u'command: kill' not in result)
        # Check if the blacklisted commands are not present
        self.assert_(u'command: command_list_begin' not in result)
        self.assert_(u'command: command_list_ok_begin' not in result)
        self.assert_(u'command: command_list_end' not in result)
        self.assert_(u'command: idle' not in result)
        self.assert_(u'command: noidle' not in result)
        self.assert_(u'command: sticker' not in result)
        self.assert_(u'OK' in result)

    def test_commands_show_less_if_auth_required_and_not_authed(self):
        settings.MPD_SERVER_PASSWORD = u'secret'
        result = self.dispatcher.handle_request(u'commands')
        # Not requiring auth
        self.assert_(u'command: close' in result, result)
        self.assert_(u'command: commands' in result, result)
        self.assert_(u'command: notcommands' in result, result)
        self.assert_(u'command: password' in result, result)
        self.assert_(u'command: ping' in result, result)
        # Requiring auth
        self.assert_(u'command: play' not in result, result)
        self.assert_(u'command: status' not in result, result)

    def test_decoders(self):
        result = self.dispatcher.handle_request(u'decoders')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_notcommands_returns_only_kill_and_ok(self):
        result = self.dispatcher.handle_request(u'notcommands')
        self.assertEqual(2, len(result))
        self.assert_(u'command: kill' in result)
        self.assert_(u'OK' in result)

    def test_notcommands_returns_more_if_auth_required_and_not_authed(self):
        settings.MPD_SERVER_PASSWORD = u'secret'
        result = self.dispatcher.handle_request(u'notcommands')
        # Not requiring auth
        self.assert_(u'command: close' not in result, result)
        self.assert_(u'command: commands' not in result, result)
        self.assert_(u'command: notcommands' not in result, result)
        self.assert_(u'command: password' not in result, result)
        self.assert_(u'command: ping' not in result, result)
        # Requiring auth
        self.assert_(u'command: play' in result, result)
        self.assert_(u'command: status' in result, result)

    def test_tagtypes(self):
        result = self.dispatcher.handle_request(u'tagtypes')
        self.assert_(u'OK' in result)

    def test_urlhandlers(self):
        result = self.dispatcher.handle_request(u'urlhandlers')
        self.assert_(u'OK' in result)
        self.assert_(u'handler: dummy:' in result)
