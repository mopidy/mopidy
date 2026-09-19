from typing import cast

import pykka
import pytest

from mopidy.core import Core, CoreListener, CoreProxy
from mopidy.models import Track
from tests import dummy_backend


@pytest.fixture
def send(mocker):
    return mocker.patch.object(CoreListener, "send")


@pytest.fixture
def backend():
    backend = dummy_backend.create_proxy()
    backend.library.dummy_library = [
        Track(uri="dummy:a"),
        Track(uri="dummy:b"),
    ]
    return backend


@pytest.fixture
def core(backend):
    config = {"core": {"max_tracklist_length": 10000}}

    yield cast(
        CoreProxy,
        Core.start(config, backends=[backend]).proxy(),
    )
    pykka.ActorRegistry.stop_all()


def test_forwards_backend_playlists_loaded_event_to_frontends(core, send):
    core.playlists_loaded().get()

    assert send.call_args[0][0] == "playlists_loaded"


def test_forwards_mixer_volume_changed_event_to_frontends(core, send):
    core.volume_changed(volume=60).get()

    assert send.call_args[0][0] == "volume_changed"
    assert send.call_args[1]["volume"] == 60


def test_forwards_mixer_mute_changed_event_to_frontends(core, send):
    core.mute_changed(mute=True).get()

    assert send.call_args[0][0] == "mute_changed"
    assert send.call_args[1]["mute"] is True


def test_tracklist_add_sends_tracklist_changed_event(core, send):
    core.tracklist.add(uris=["dummy:a"]).get()

    assert send.call_args[0][0] == "tracklist_changed"


def test_tracklist_clear_sends_tracklist_changed_event(core, send):
    core.tracklist.add(uris=["dummy:a"]).get()

    core.tracklist.clear().get()

    assert send.call_args[0][0] == "tracklist_changed"


def test_tracklist_move_sends_tracklist_changed_event(core, send):
    core.tracklist.add(uris=["dummy:a", "dummy:b"]).get()

    core.tracklist.move(0, 1, 1).get()

    assert send.call_args[0][0] == "tracklist_changed"


def test_tracklist_remove_sends_tracklist_changed_event(core, send):
    core.tracklist.add(uris=["dummy:a"]).get()

    core.tracklist.remove({"uri": ["dummy:a"]}).get()

    assert send.call_args[0][0] == "tracklist_changed"


def test_tracklist_shuffle_sends_tracklist_changed_event(core, send):
    core.tracklist.add(uris=["dummy:a", "dummy:b"]).get()

    core.tracklist.shuffle().get()

    assert send.call_args[0][0] == "tracklist_changed"


def test_playlists_refresh_sends_playlists_loaded_event(core, send):
    core.playlists.refresh().get()

    assert send.call_args[0][0] == "playlists_loaded"


def test_playlists_refresh_uri_sends_playlists_loaded_event(core, send):
    core.playlists.refresh(uri_scheme="dummy").get()

    assert send.call_args[0][0] == "playlists_loaded"


def test_playlists_create_sends_playlist_changed_event(core, send):
    core.playlists.create("foo").get()

    assert send.call_args[0][0] == "playlist_changed"


def test_playlists_delete_sends_playlist_deleted_event(core, send):
    playlist = core.playlists.create("foo").get()
    core.playlists.delete(playlist.uri).get()

    assert send.call_args[0][0] == "playlist_deleted"


def test_playlists_save_sends_playlist_changed_event(core, send):
    playlist = core.playlists.create("foo").get()
    playlist = playlist.replace(name="bar")

    core.playlists.save(playlist).get()

    assert send.call_args[0][0] == "playlist_changed"
