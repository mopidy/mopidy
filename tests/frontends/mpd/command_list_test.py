import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import dispatcher
from mopidy.mixers.dummy import DummyMixer

class CommandListsTest(unittest.TestCase):
    def setUp(self):
        self.b = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.dispatcher = dispatcher.MpdDispatcher()

    def tearDown(self):
        self.b.stop().get()
        self.mixer.stop().get()

    def test_command_list_begin(self):
        result = self.dispatcher.handle_request(u'command_list_begin')
        self.assertEquals(result, [])

    def test_command_list_end(self):
        self.dispatcher.handle_request(u'command_list_begin')
        result = self.dispatcher.handle_request(u'command_list_end')
        self.assert_(u'OK' in result)

    def test_command_list_end_without_start_first_is_an_unknown_command(self):
        result = self.dispatcher.handle_request(u'command_list_end')
        self.assertEquals(result[0],
            u'ACK [5@0] {} unknown command "command_list_end"')

    def test_command_list_with_ping(self):
        self.dispatcher.handle_request(u'command_list_begin')
        self.assertEqual([], self.dispatcher.command_list)
        self.assertEqual(False, self.dispatcher.command_list_ok)
        self.dispatcher.handle_request(u'ping')
        self.assert_(u'ping' in self.dispatcher.command_list)
        result = self.dispatcher.handle_request(u'command_list_end')
        self.assert_(u'OK' in result)
        self.assertEqual(False, self.dispatcher.command_list)

    def test_command_list_with_error_returns_ack_with_correct_index(self):
        self.dispatcher.handle_request(u'command_list_begin')
        self.dispatcher.handle_request(u'play') # Known command
        self.dispatcher.handle_request(u'paly') # Unknown command
        result = self.dispatcher.handle_request(u'command_list_end')
        self.assertEqual(len(result), 1, result)
        self.assertEqual(result[0], u'ACK [5@1] {} unknown command "paly"')

    def test_command_list_ok_begin(self):
        result = self.dispatcher.handle_request(u'command_list_ok_begin')
        self.assertEquals(result, [])

    def test_command_list_ok_with_ping(self):
        self.dispatcher.handle_request(u'command_list_ok_begin')
        self.assertEqual([], self.dispatcher.command_list)
        self.assertEqual(True, self.dispatcher.command_list_ok)
        self.dispatcher.handle_request(u'ping')
        self.assert_(u'ping' in self.dispatcher.command_list)
        result = self.dispatcher.handle_request(u'command_list_end')
        self.assert_(u'list_OK' in result)
        self.assert_(u'OK' in result)
        self.assertEqual(False, self.dispatcher.command_list)
        self.assertEqual(False, self.dispatcher.command_list_ok)
