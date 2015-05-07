from __future__ import absolute_import, unicode_literals

import unittest

import pykka

from mopidy import core
from mopidy.internal import deprecation
from mopidy.mpd.dispatcher import MpdDispatcher
from mopidy.mpd.exceptions import MpdAckError

from tests import dummy_backend


class MpdDispatcherTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        config = {
            'mpd': {
                'password': None,
                'command_blacklist': ['disabled'],
            }
        }
        self.backend = dummy_backend.create_proxy()
        self.dispatcher = MpdDispatcher(config=config)

        with deprecation.ignore():
            self.core = core.Core.start(backends=[self.backend]).proxy()

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def test_call_handler_for_unknown_command_raises_exception(self):
        with self.assertRaises(MpdAckError) as cm:
            self.dispatcher._call_handler('an_unknown_command with args')

        self.assertEqual(
            cm.exception.get_mpd_ack(),
            'ACK [5@0] {} unknown command "an_unknown_command"')

    def test_handling_unknown_request_yields_error(self):
        result = self.dispatcher.handle_request('an unhandled request')
        self.assertEqual(result[0], 'ACK [5@0] {} unknown command "an"')

    def test_handling_blacklisted_command(self):
        result = self.dispatcher.handle_request('disabled')
        self.assertEqual(result[0], 'ACK [0@0] {disabled} "disabled" has been '
                         'disabled in the server')
