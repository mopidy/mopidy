import json

from pytest_mock import MockerFixture

from mopidy.http import actor


def test_track_playback_paused_is_broadcasted(mocker: MockerFixture) -> None:
    broadcast = mocker.patch("mopidy.http.handlers.WebSocketHandler.broadcast")
    io_loop = mocker.Mock()

    actor.on_event("track_playback_paused", io_loop, foo="bar")

    assert json.loads(broadcast.call_args[0][0]) == {
        "event": "track_playback_paused",
        "foo": "bar",
    }


def test_track_playback_resumed_is_broadcasted(mocker: MockerFixture) -> None:
    broadcast = mocker.patch("mopidy.http.handlers.WebSocketHandler.broadcast")
    io_loop = mocker.Mock()

    actor.on_event("track_playback_resumed", io_loop, foo="bar")

    assert json.loads(broadcast.call_args[0][0]) == {
        "event": "track_playback_resumed",
        "foo": "bar",
    }
