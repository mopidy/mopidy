import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer

class ReflectionHandlerTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.h = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_commands_returns_list_of_all_commands(self):
        result = self.h.handle_request(u'commands')
        # Check if some random commands are included
        self.assert_(u'command: commands' in result)
        self.assert_(u'command: play' in result)
        self.assert_(u'command: status' in result)
        # Check if the blacklisted commands are not present
        self.assert_(u'command: command_list_begin' not in result)
        self.assert_(u'command: command_list_ok_begin' not in result)
        self.assert_(u'command: command_list_end' not in result)
        self.assert_(u'command: idle' not in result)
        self.assert_(u'command: noidle' not in result)
        self.assert_(u'command: sticker' not in result)
        self.assert_(u'OK' in result)

    def test_decoders(self):
        result = self.h.handle_request(u'decoders')
        self.assert_(u'ACK [0@0] {} Not implemented' in result)

    def test_notcommands_returns_only_ok(self):
        result = self.h.handle_request(u'notcommands')
        self.assertEqual(1, len(result))
        self.assert_(u'OK' in result)

    def test_tagtypes(self):
        result = self.h.handle_request(u'tagtypes')
        self.assert_(u'OK' in result)

    def test_urlhandlers(self):
        result = self.h.handle_request(u'urlhandlers')
        self.assert_(u'OK' in result)
        self.assert_(u'handler: dummy:' in result)
