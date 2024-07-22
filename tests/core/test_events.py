import unittest
from typing import cast
from unittest import mock

import pykka
from mopidy import core
from mopidy.internal import deprecation
from mopidy.models import Track

from tests import dummy_backend


@mock.patch.object(core.CoreListener, "send")
class BackendEventsTest(unittest.TestCase):
    def setUp(self):
        config = {"core": {"max_tracklist_length": 10000}}

        self.backend = dummy_backend.create_proxy()
        self.backend.library.dummy_library = [
            Track(uri="dummy:a"),
            Track(uri="dummy:b"),
        ]

        with deprecation.ignore():
            self.core = cast(
                core.CoreProxy, core.Core.start(config, backends=[self.backend]).proxy()
            )

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_forwards_backend_playlists_loaded_event_to_frontends(self, send):
        self.core.playlists_loaded().get()

        assert send.call_args[0][0] == "playlists_loaded"

    def test_forwards_mixer_volume_changed_event_to_frontends(self, send):
        self.core.volume_changed(volume=60).get()

        assert send.call_args[0][0] == "volume_changed"
        assert send.call_args[1]["volume"] == 60

    def test_forwards_mixer_mute_changed_event_to_frontends(self, send):
        self.core.mute_changed(mute=True).get()

        assert send.call_args[0][0] == "mute_changed"
        assert send.call_args[1]["mute"] is True

    def test_tracklist_add_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(uris=["dummy:a"]).get()

        assert send.call_args[0][0] == "tracklist_changed"

    def test_tracklist_clear_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(uris=["dummy:a"]).get()

        self.core.tracklist.clear().get()

        assert send.call_args[0][0] == "tracklist_changed"

    def test_tracklist_move_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(uris=["dummy:a", "dummy:b"]).get()

        self.core.tracklist.move(0, 1, 1).get()

        assert send.call_args[0][0] == "tracklist_changed"

    def test_tracklist_remove_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(uris=["dummy:a"]).get()

        self.core.tracklist.remove({"uri": ["dummy:a"]}).get()

        assert send.call_args[0][0] == "tracklist_changed"

    def test_tracklist_shuffle_sends_tracklist_changed_event(self, send):
        self.core.tracklist.add(uris=["dummy:a", "dummy:b"]).get()

        self.core.tracklist.shuffle().get()

        assert send.call_args[0][0] == "tracklist_changed"

    def test_playlists_refresh_sends_playlists_loaded_event(self, send):
        self.core.playlists.refresh().get()

        assert send.call_args[0][0] == "playlists_loaded"

    def test_playlists_refresh_uri_sends_playlists_loaded_event(self, send):
        self.core.playlists.refresh(uri_scheme="dummy").get()

        assert send.call_args[0][0] == "playlists_loaded"

    def test_playlists_create_sends_playlist_changed_event(self, send):
        self.core.playlists.create("foo").get()

        assert send.call_args[0][0] == "playlist_changed"

    def test_playlists_delete_sends_playlist_deleted_event(self, send):
        playlist = self.core.playlists.create("foo").get()
        self.core.playlists.delete(playlist.uri).get()

        assert send.call_args[0][0] == "playlist_deleted"

    def test_playlists_save_sends_playlist_changed_event(self, send):
        playlist = self.core.playlists.create("foo").get()
        playlist = playlist.replace(name="bar")

        self.core.playlists.save(playlist).get()

        assert send.call_args[0][0] == "playlist_changed"
