import unittest

from mopidy.backends.dummy import DummyBackend
from mopidy.frontends.mpd import frontend, MpdAckError
from mopidy.mixers.dummy import DummyMixer

class RequestHandlerTest(unittest.TestCase):
    def setUp(self):
        self.m = DummyMixer()
        self.b = DummyBackend(mixer=self.m)
        self.h = frontend.MpdFrontend(backend=self.b)

    def test_register_same_pattern_twice_fails(self):
        func = lambda: None
        try:
            frontend.handle_pattern('a pattern')(func)
            frontend.handle_pattern('a pattern')(func)
            self.fail('Registering a pattern twice shoulde raise ValueError')
        except ValueError:
            pass

    def test_finding_handler_for_unknown_command_raises_exception(self):
        try:
            self.h.find_handler('an_unknown_command with args')
            self.fail('Should raise exception')
        except MpdAckError as e:
            self.assertEqual(e.get_mpd_ack(),
                u'ACK [5@0] {} unknown command "an_unknown_command"')

    def test_finding_handler_for_known_command_returns_handler_and_kwargs(self):
        expected_handler = lambda x: None
        frontend._request_handlers['known_command (?P<arg1>.+)'] = \
            expected_handler
        (handler, kwargs) = self.h.find_handler('known_command an_arg')
        self.assertEqual(handler, expected_handler)
        self.assert_('arg1' in kwargs)
        self.assertEqual(kwargs['arg1'], 'an_arg')

    def test_handling_unknown_request_yields_error(self):
        result = self.h.handle_request('an unhandled request')
        self.assertEqual(result[0], u'ACK [5@0] {} unknown command "an"')

    def test_handling_known_request(self):
        expected = 'magic'
        frontend._request_handlers['known request'] = lambda x: expected
        result = self.h.handle_request('known request')
        self.assert_(u'OK' in result)
        self.assert_(expected in result)
