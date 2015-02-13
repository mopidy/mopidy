from __future__ import absolute_import, unicode_literals

import unittest

import mock

import pykka

from mopidy import core
from mopidy.models import Track

from tests import dummy_backend


@mock.patch.object(core.CoreListener, 'send')
class BackendEventsTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.backend = dummy_backend.create_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def test_forwards_backend_playlists_loaded_event_to_frontends(self, send):
        self.core.playlists_loaded().get()

        self.assertEqual(send.call_args[0][0], 'playlists_loaded')

    def test_forwards_mixer_volume_changed_event_to_frontends(self, send):
        self.core.volume_changed(volume=60).get()

        self.assertEqual(send.call_args[0][0], 'volume_changed')
        self.assertEqual(send.call_args[1]['volume'], 60)

    def test_forwards_mixer_mute_changed_event_to_frontends(self, send):
        self.core.mute_changed(mute=True).get()

        self.assertEqual(send.call_args[0][0], 'mute_changed')
        self.assertEqual(send.call_args[1]['mute'], True)

    def test_tracklist_add_sends_tracklist_changed_event(self, send):
        send.reset_mock()

        self.core.tracklist.add([Track(uri='dummy:a')]).get()

        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_clear_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add([Track(uri='dummy:a')]).get()
        send.reset_mock()

        self.core.tracklist.clear().get()

        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_move_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(
            [Track(uri='dummy:a'), Track(uri='dummy:b')]).get()
        send.reset_mock()

        self.core.tracklist.move(0, 1, 1).get()

        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_remove_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add([Track(uri='dummy:a')]).get()
        send.reset_mock()

        self.core.tracklist.remove(uri=['dummy:a']).get()

        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_tracklist_shuffle_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(
            [Track(uri='dummy:a'), Track(uri='dummy:b')]).get()
        send.reset_mock()

        self.core.tracklist.shuffle().get()

        self.assertEqual(send.call_args[0][0], 'tracklist_changed')

    def test_playlists_refresh_sends_playlists_loaded_event(self, send):
        send.reset_mock()

        self.core.playlists.refresh().get()

        self.assertEqual(send.call_args[0][0], 'playlists_loaded')

    def test_playlists_refresh_uri_sends_playlists_loaded_event(self, send):
        send.reset_mock()

        self.core.playlists.refresh(uri_scheme='dummy').get()

        self.assertEqual(send.call_args[0][0], 'playlists_loaded')

    def test_playlists_create_sends_playlist_changed_event(self, send):
        send.reset_mock()

        self.core.playlists.create('foo').get()

        self.assertEqual(send.call_args[0][0], 'playlist_changed')

    @unittest.SkipTest
    def test_playlists_delete_sends_playlist_deleted_event(self, send):
        # TODO We should probably add a playlist_deleted event
        pass

    def test_playlists_save_sends_playlist_changed_event(self, send):
        playlist = self.core.playlists.create('foo').get()
        playlist = playlist.copy(name='bar')
        send.reset_mock()

        self.core.playlists.save(playlist).get()

        self.assertEqual(send.call_args[0][0], 'playlist_changed')
