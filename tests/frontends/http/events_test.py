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
        self.http.track_playback_paused(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'track_playback_paused',
                'foo': 'bar',
            })

    def test_track_playback_resumed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.track_playback_resumed(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'track_playback_resumed',
                'foo': 'bar',
            })

    def test_track_playback_started_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.track_playback_started(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'track_playback_started',
                'foo': 'bar',
            })

    def test_track_playback_ended_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.track_playback_ended(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'track_playback_ended',
                'foo': 'bar',
            })

    def test_playback_state_changed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.playback_state_changed(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'playback_state_changed',
                'foo': 'bar',
            })

    def test_tracklist_changed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.tracklist_changed(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'tracklist_changed',
                'foo': 'bar',
            })

    def test_playlists_loaded_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.playlists_loaded(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'playlists_loaded',
                'foo': 'bar',
            })

    def test_playlist_changed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.playlist_changed(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'playlist_changed',
                'foo': 'bar',
            })

    def test_options_changed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.options_changed(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'options_changed',
                'foo': 'bar',
            })

    def test_volume_changed_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.volume_changed(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'volume_changed',
                'foo': 'bar',
            })

    def test_seeked_is_broadcasted(self, publish):
        publish.reset_mock()
        self.http.seeked(foo='bar')
        self.assertEqual(publish.call_args[0][0], 'websocket-broadcast')
        self.assertDictEqual(
            json.loads(str(publish.call_args[0][1])), {
                'event': 'seeked',
                'foo': 'bar',
            })
