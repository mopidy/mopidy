from __future__ import absolute_import, unicode_literals

import mock

import pytest

from mopidy.mpd import actor

# NOTE: Should be kept in sync with all events from mopidy.core.listener


@pytest.mark.parametrize("event,expected,hostname", [
    (['track_playback_paused', 'tl_track', 'time_position'], None, 'foobar'),
    (['track_playback_resumed', 'tl_track', 'time_position'], None, 'foobar'),
    (['track_playback_started', 'tl_track'], None, 'foobar'),
    (['track_playback_ended', 'tl_track', 'time_position'], None, 'foobar'),
    (['playback_state_changed', 'old_state', 'new_state'], 'player', 'foobar'),
    (['tracklist_changed'], 'playlist', 'foobar'),
    (['playlists_loaded'], 'stored_playlist', 'foobar'),
    (['playlist_changed', 'playlist'], 'stored_playlist', 'foobar'),
    (['playlist_deleted', 'uri'], 'stored_playlist', 'foobar'),
    (['options_changed'], 'options', 'foobar'),
    (['volume_changed', 'volume'], 'mixer', 'foobar'),
    (['mute_changed', 'mute'], 'output', 'foobar'),
    (['seeked', 'time_position'], 'player', 'foobar'),
    (['stream_title_changed', 'title'], 'playlist', 'foobar'),

    (['track_playback_paused', 'tl_track', 'time_position'], None,
        'unix:foobar'),
    (['track_playback_resumed', 'tl_track', 'time_position'], None,
        'unix:foobar'),
    (['track_playback_started', 'tl_track'], None, 'unix:foobar'),
    (['track_playback_ended', 'tl_track', 'time_position'], None,
        'unix:foobar'),
    (['playback_state_changed', 'old_state', 'new_state'], 'player',
        'unix:foobar'),
    (['tracklist_changed'], 'playlist', 'unix:foobar'),
    (['playlists_loaded'], 'stored_playlist', 'unix:foobar'),
    (['playlist_changed', 'playlist'], 'stored_playlist', 'unix:foobar'),
    (['playlist_deleted', 'uri'], 'stored_playlist', 'unix:foobar'),
    (['options_changed'], 'options', 'unix:foobar'),
    (['volume_changed', 'volume'], 'mixer', 'unix:foobar'),
    (['mute_changed', 'mute'], 'output', 'unix:foobar'),
    (['seeked', 'time_position'], 'player', 'unix:foobar'),
    (['stream_title_changed', 'title'], 'playlist', 'unix:foobar'),
])
def test_idle_hooked_up_correctly(event, expected, hostname):
    config = {'mpd': {'hostname': hostname,
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
