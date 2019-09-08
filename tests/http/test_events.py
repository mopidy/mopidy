from __future__ import absolute_import, unicode_literals

import json
import unittest

import mock

from mopidy.http import actor


@mock.patch('mopidy.http.handlers.WebSocketHandler.broadcast')
class HttpEventsTest(unittest.TestCase):

    def setUp(self):
        self.loop = mock.Mock()

    def test_track_playback_paused_is_broadcasted(self, broadcast):
        actor.on_event('track_playback_paused', self.loop, foo='bar')

        self.assertDictEqual(
            json.loads(str(broadcast.call_args[0][1])), {
                'event': 'track_playback_paused',
                'foo': 'bar',
            })

    def test_track_playback_resumed_is_broadcasted(self, broadcast):
        actor.on_event('track_playback_resumed', self.loop, foo='bar')

        self.assertDictEqual(
            json.loads(str(broadcast.call_args[0][1])), {
                'event': 'track_playback_resumed',
                'foo': 'bar',
            })
