import json

try:
    import cherrypy
except ImportError:
    cherrypy = False
try:
    import ws4py
except ImportError:
    ws4py = False
import mock

from mopidy.exceptions import OptionalDependencyError
try:
    from mopidy.frontends.http import actor
except OptionalDependencyError:
    pass

from tests import unittest


@unittest.skipUnless(cherrypy, 'cherrypy not found')
@unittest.skipUnless(ws4py, 'ws4py not found')
@mock.patch('cherrypy.engine.publish')
class HttpEventsTest(unittest.TestCase):
    def setUp(self):
        self.http = actor.HttpFrontend(core=mock.Mock())

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
