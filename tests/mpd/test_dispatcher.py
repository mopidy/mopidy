from __future__ import unicode_literals

import unittest

import pykka

from mopidy import core
from mopidy.backend import dummy
from mopidy.mpd.dispatcher import MpdDispatcher
from mopidy.mpd.exceptions import MpdAckError


class MpdDispatcherTest(unittest.TestCase):
    def setUp(self):
        config = {
            'mpd': {
                'password': None,
            }
        }
        self.backend = dummy.create_dummy_backend_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.dispatcher = MpdDispatcher(config=config)

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_call_handler_for_unknown_command_raises_exception(self):
        try:
            self.dispatcher._call_handler('an_unknown_command with args')
            self.fail('Should raise exception')
        except MpdAckError as e:
            self.assertEqual(
                e.get_mpd_ack(),
                'ACK [5@0] {} unknown command "an_unknown_command"')

    def test_handling_unknown_request_yields_error(self):
        result = self.dispatcher.handle_request('an unhandled request')
        self.assertEqual(result[0], 'ACK [5@0] {} unknown command "an"')
