import json

import cherrypy
import mock

from mopidy.frontends.http import HttpFrontend

from tests import unittest


@mock.patch.object(cherrypy.engine, 'publish')
class HttpEventsTest(unittest.TestCase):
    def setUp(self):
        self.http = HttpFrontend(core=mock.Mock())

    def test_track_playback_paused_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.on_event('track_playback_paused', foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'track_playback_paused',
                'foo': 'bar',
            })

    def test_track_playback_resumed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.on_event('track_playback_resumed', foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'track_playback_resumed',
                'foo': 'bar',
            })
