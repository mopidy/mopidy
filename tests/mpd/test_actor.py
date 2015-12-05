from __future__ import absolute_import, unicode_literals

import mock

import pytest

from mopidy.mpd import actor

# NOTE: Should be kept in sync with all events from mopidy.core.listener


@pytest.mark.parametrize("event,expected", [
    (['track_playback_paused', 'tl_track', 'time_position'], None),
    (['track_playback_resumed', 'tl_track', 'time_position'], None),
    (['track_playback_started', 'tl_track'], None),
    (['track_playback_ended', 'tl_track', 'time_position'], None),
    (['playback_state_changed', 'old_state', 'new_state'], 'player'),
    (['tracklist_changed'], 'playlist'),
    (['playlists_loaded'], 'stored_playlist'),
    (['playlist_changed', 'playlist'], 'stored_playlist'),
    (['playlist_deleted', 'uri'], 'stored_playlist'),
    (['options_changed'], 'options'),
    (['volume_changed', 'volume'], 'mixer'),
    (['mute_changed', 'mute'], 'output'),
    (['seeked', 'time_position'], 'player'),
    (['stream_title_changed', 'title'], 'playlist'),
])
def test_idle_hooked_up_correctly(event, expected):
    config = {'mpd': {'hostname': 'foobar',
                      'port': 1234,
                      'zeroconf': None,
                      'max_connections': None,
                      'connection_timeout': None}}

    with mock.patch.object(actor.MpdFrontend, '_setup_server'):
        frontend = actor.MpdFrontend(core=mock.Mock(), config=config)

    with mock.patch('mopidy.listener.send') as send_mock:
        frontend.on_event(event[0], **{e: None for e in event[1:]})

    if expected is None:
        assert not send_mock.call_args
    else:
        send_mock.assert_called_once_with(mock.ANY, expected)
