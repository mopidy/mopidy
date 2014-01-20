from __future__ import unicode_literals

import mock
import unittest

import pykka

from mopidy import core
from mopidy.backend import dummy
from mopidy.models import Track


@mock.patch.object(core.CoreListener, 'send')
class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        self.backend = dummy.create_dummy_backend_proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_backends_playlists_loaded_forwards_event_to_frontends(self, send):
        self.core.playlists_loaded().get()

        self.assertEqual(send.call_args[0][0], 'playlists_loaded')

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
