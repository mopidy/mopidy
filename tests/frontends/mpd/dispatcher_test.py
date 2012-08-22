from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd.dispatcher import MpdDispatcher
from mopidy.frontends.mpd.exceptions import MpdAckError
from mopidy.frontends.mpd.protocol import request_handlers, handle_request
from mopidy.mixers.dummy import DummyMixer

from tests import unittest


class MpdDispatcherTest(unittest.TestCase):
    def setUp(self):
        self.backend = DummyBackend.start().proxy()
        self.mixer = DummyMixer.start().proxy()
        self.dispatcher = MpdDispatcher()

    def tearDown(self):
        self.backend.stop().get()
        self.mixer.stop().get()

    def test_register_same_pattern_twice_fails(self):
        func = lambda: None
        try:
            handle_request('a pattern')(func)
            handle_request('a pattern')(func)
            self.fail('Registering a pattern twice shoulde raise ValueError')
        except ValueError:
            pass

    def test_finding_handler_for_unknown_command_raises_exception(self):
        try:
            self.dispatcher._find_handler('an_unknown_command with args')
            self.fail('Should raise exception')
        except MpdAckError as e:
            self.assertEqual(e.get_mpd_ack(),
                u'ACK [5@0] {} unknown command "an_unknown_command"')

    def test_finding_handler_for_known_command_returns_handler_and_kwargs(self):
        expected_handler = lambda x: None
        request_handlers['known_command (?P<arg1>.+)'] = \
            expected_handler
        (handler, kwargs) = self.dispatcher._find_handler('known_command an_arg')
        self.assertEqual(handler, expected_handler)
        self.assert_('arg1' in kwargs)
        self.assertEqual(kwargs['arg1'], 'an_arg')

    def test_handling_unknown_request_yields_error(self):
        result = self.dispatcher.handle_request('an unhandled request')
        self.assertEqual(result[0], u'ACK [5@0] {} unknown command "an"')

    def test_handling_known_request(self):
        expected = 'magic'
        request_handlers['known request'] = lambda x: expected
        result = self.dispatcher.handle_request('known request')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)
