from unittest import mock

import pytest

from mopidy.core import CoreListener
from mopidy.models import TlTrack
from mopidy.types import PlaybackState, Uri
from tests.factories import PlaylistFactory, TrackFactory


@pytest.fixture
def listener():
    return CoreListener()


@pytest.fixture
def tl_track():
    return TlTrack(tlid=1, track=TrackFactory.build())


def test_on_event_forwards_to_specific_handler(listener, tl_track):
    listener.track_playback_paused = mock.Mock()

    listener.on_event("track_playback_paused", track=tl_track, position=0)

    listener.track_playback_paused.assert_called_with(
        track=tl_track,
        position=0,
    )


def test_listener_has_default_impl_for_track_playback_paused(listener, tl_track):
    listener.track_playback_paused(tl_track, 0)


def test_listener_has_default_impl_for_track_playback_resumed(listener, tl_track):
    listener.track_playback_resumed(tl_track, 0)


def test_listener_has_default_impl_for_track_playback_started(listener, tl_track):
    listener.track_playback_started(tl_track)


def test_listener_has_default_impl_for_track_playback_ended(listener, tl_track):
    listener.track_playback_ended(tl_track, 0)


def test_listener_has_default_impl_for_playback_state_changed(listener):
    listener.playback_state_changed(
        PlaybackState.STOPPED,
        PlaybackState.PLAYING,
    )


def test_listener_has_default_impl_for_tracklist_changed(listener):
    listener.tracklist_changed()


def test_listener_has_default_impl_for_playlists_loaded(listener):
    listener.playlists_loaded()


def test_listener_has_default_impl_for_playlist_changed(listener):
    listener.playlist_changed(PlaylistFactory.build())


def test_listener_has_default_impl_for_playlist_deleted(listener):
    listener.playlist_deleted(Uri("dummy:playlist"))


def test_listener_has_default_impl_for_options_changed(listener):
    listener.options_changed()


def test_listener_has_default_impl_for_volume_changed(listener):
    listener.volume_changed(70)


def test_listener_has_default_impl_for_mute_changed(listener):
    listener.mute_changed(True)


def test_listener_has_default_impl_for_seeked(listener):
    listener.seeked(0)


def test_listener_has_default_impl_for_stream_title_changed(listener):
    listener.stream_title_changed("foobar")
