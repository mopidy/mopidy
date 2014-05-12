from __future__ import unicode_literals

import json
import unittest

import mock


try:
    import tornado
except ImportError:
    tornado = False

if tornado:
    from mopidy.http import actor


@unittest.skipUnless(tornado, 'tornado is missing')
@mock.patch('mopidy.http.handlers.WebSocketHandler.broadcast')
class HttpEventsTest(unittest.TestCase):
    def setUp(self):
        config = {
            'http': {
                'hostname': '127.0.0.1',
                'port': 6680,
                'static_dir': None,
                'allow_draft76': True,
                'zeroconf': '',
            }
        }
        self.http = actor.HttpFrontend(config=config, core=mock.Mock())

    def test_track_playback_paused_is_broadcasted(self, broadcast):
        broadcast.reset_mock()
        self.http.on_event('track_playback_paused', foo='bar')
        self.assertEqual(broadcast.call_args[0][0], set([]))
        self.assertDictEqual(
            json.loads(str(broadcast.call_args[0][1])), {
                'event': 'track_playback_paused',
                'foo': 'bar',
            })

    def test_track_playback_resumed_is_broadcasted(self, broadcast):
        broadcast.reset_mock()
        self.http.on_event('track_playback_resumed', foo='bar')
        self.assertEqual(broadcast.call_args[0][0], set([]))
        self.assertDictEqual(
            json.loads(str(broadcast.call_args[0][1])), {
                'event': 'track_playback_resumed',
                'foo': 'bar',
            })
