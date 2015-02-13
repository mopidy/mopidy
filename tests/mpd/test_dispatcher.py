from __future__ import absolute_import, unicode_literals

import unittest

import pykka

from mopidy import core
from mopidy.mpd.dispatcher import MpdDispatcher
from mopidy.mpd.exceptions import MpdAckError

from tests import dummy_backend


class MpdDispatcherTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        config = {
            'mpd': {
                'password': None,
            }
        }
        self.backend = dummy_backend.create_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.dispatcher = MpdDispatcher(config=config)

    def tearDown(self):  # noqa: N802
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
