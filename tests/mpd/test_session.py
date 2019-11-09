import logging
from unittest.mock import Mock, sentinel

from mopidy.internal import network
from mopidy.mpd import dispatcher, session


def test_on_start_logged(caplog):
    caplog.set_level(logging.INFO)
    connection = Mock(spec=network.Connection)

    session.MpdSession(connection).on_start()

    assert f"New MPD connection from {connection}" in caplog.text


def test_on_line_received_logged(caplog):
    caplog.set_level(logging.DEBUG)
    connection = Mock(spec=network.Connection)
    mpd_session = session.MpdSession(connection)
    mpd_session.dispatcher = Mock(spec=dispatcher.MpdDispatcher)
    mpd_session.dispatcher.handle_request.return_value = [str(sentinel.resp)]

    mpd_session.on_line_received(sentinel.line)

    assert f"Request from {connection}: {sentinel.line}" in caplog.text
    assert f"Response to {connection}:" in caplog.text
