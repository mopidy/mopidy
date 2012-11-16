from __future__ import unicode_literals

import pykka

from tests import unittest

from mopidy import core
from mopidy.backends import dummy
from mopidy.frontends.http import api
from mopidy.models import Track


class ApiResourceTest(unittest.TestCase):
    def setUp(self):
        self.backend = dummy.DummyBackend.start(audio=None).proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.api = api.ApiResource(core=self.core)

        self.core.playlists.create('x')
        self.core.playlists.create('y')
        self.core.playlists.create('z')
        self.core.tracklist.append([
            Track(uri='dummy:a'),
            Track(uri='dummy:b'),
            Track(uri='dummy:c'),
        ])

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_api_get_returns_list_of_resources(self):
        result = self.api.GET()

        self.assertIn('resources', result)

        self.assertIn('player', result['resources'])
        self.assertEquals(
            '/api/player/', result['resources']['player']['href'])

        self.assertIn('tracklist', result['resources'])
        self.assertEquals(
            '/api/tracklist/', result['resources']['tracklist']['href'])

        self.assertIn('playlists', result['resources'])
        self.assertEquals(
            '/api/playlists/', result['resources']['playlists']['href'])

    def test_player_get_returns_playback_properties(self):
        result = self.api.player.GET()

        self.assertIn('properties', result)

        self.assertIn('state', result['properties'])
        self.assertEqual('stopped', result['properties']['state'])

        self.assertIn('currentTrack', result['properties'])
        self.assertEqual(None, result['properties']['currentTrack'])

        self.assertIn('consume', result['properties'])
        self.assertEqual(False, result['properties']['consume'])

        self.assertIn('random', result['properties'])
        self.assertEqual(False, result['properties']['random'])

        self.assertIn('repeat', result['properties'])
        self.assertEqual(False, result['properties']['repeat'])

        self.assertIn('single', result['properties'])
        self.assertEqual(False, result['properties']['single'])

        self.assertIn('volume', result['properties'])
        self.assertEqual(None, result['properties']['volume'])

        self.assertIn('timePosition', result['properties'])
        self.assertEqual(0, result['properties']['timePosition'])

    def test_player_state_changes_when_playing(self):
        self.core.playback.play()

        result = self.api.player.GET()

        self.assertEqual('playing', result['properties']['state'])

    def test_player_volume_changes(self):
        self.core.playback.volume = 37

        result = self.api.player.GET()

        self.assertEqual(37, result['properties']['volume'])

    def test_tracklist_returns_tracklist(self):
        result = self.api.tracklist.GET()

        self.assertIn('tracks', result)
        self.assertEqual(3, len(result['tracks']))

        self.assertEqual('dummy:a', result['tracks'][0]['uri'])
        self.assertEqual(0, result['tracks'][0]['tlid'])

        self.assertEqual('dummy:b', result['tracks'][1]['uri'])
        self.assertEqual(1, result['tracks'][1]['tlid'])

        self.assertEqual('dummy:c', result['tracks'][2]['uri'])
        self.assertEqual(2, result['tracks'][2]['tlid'])

    def test_tracklist_includes_current_track(self):
        self.core.playback.play()

        result = self.api.tracklist.GET()

        self.assertIn('currentTrackTlid', result)
        self.assertEqual(0, result['currentTrackTlid'])

    def test_playlists_returns_playlists(self):
        result = self.api.playlists.GET()

        self.assertIn('playlists', result)
        self.assertEqual('x', result['playlists'][0]['name'])
        self.assertEqual('y', result['playlists'][1]['name'])
        self.assertEqual('z', result['playlists'][2]['name'])
