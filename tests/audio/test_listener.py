from unittest import mock

import pytest

from mopidy import audio


@pytest.fixture
def listener():
    return audio.AudioListener()


def test_on_event_forwards_to_specific_handler(listener):
    listener.state_changed = mock.Mock()

    listener.on_event(
        "state_changed",
        old_state="stopped",
        new_state="playing",
        target_state=None,
    )

    listener.state_changed.assert_called_with(
        old_state="stopped",
        new_state="playing",
        target_state=None,
    )


def test_listener_has_default_impl_for_reached_end_of_stream(listener):
    listener.reached_end_of_stream()


def test_listener_has_default_impl_for_state_changed(listener):
    listener.state_changed(None, None, None)


def test_listener_has_default_impl_for_stream_changed(listener):
    listener.stream_changed(None)


def test_listener_has_default_impl_for_position_changed(listener):
    listener.position_changed(None)


def test_listener_has_default_impl_for_tags_changed(listener):
    listener.tags_changed([])
