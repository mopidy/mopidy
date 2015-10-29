from __future__ import unicode_literals

import contextlib
import re
import warnings

from mopidy import compat


# Messages used in deprecation warnings are collected here so we can target
# them easily when ignoring warnings.
_MESSAGES = {
    # Deprecated features mpd:
    'mpd.protocol.playback.pause:state_arg':
        'The use of pause command w/o the PAUSE argument is deprecated.',
    'mpd.protocol.current_playlist.playlist':
        'Do not use this, instead use playlistinfo',

    # Deprecated features in audio:
    'audio.emit_end_of_stream': 'audio.emit_end_of_stream() is deprecated',

    # Deprecated features in core libary:
    'core.library.find_exact': 'library.find_exact() is deprecated',
    'core.library.lookup:uri_arg':
        'library.lookup() "uri" argument is deprecated',
    'core.library.search:kwargs_query':
        'library.search() with "kwargs" as query is deprecated',
    'core.library.search:empty_query':
        'library.search() with empty "query" argument deprecated',

    # Deprecated features in core playback:
    'core.playback.get_mute': 'playback.get_mute() is deprecated',
    'core.playback.set_mute': 'playback.set_mute() is deprecated',
    'core.playback.get_volume': 'playback.get_volume() is deprecated',
    'core.playback.set_volume': 'playback.set_volume() is deprecated',
    'core.playback.play:tl_track_kwargs':
        'playback.play() with "tl_track" argument is pending deprecation use '
        '"tlid" instead',

    # Deprecated features in core playlists:
    'core.playlists.filter': 'playlists.filter() is deprecated',
    'core.playlists.get_playlists': 'playlists.get_playlists() is deprecated',

    # Deprecated features in core tracklist:
    'core.tracklist.add:tracks_arg':
        'tracklist.add() "tracks" argument is deprecated',
    'core.tracklist.add:uri_arg':
        'tracklist.add() "uri" argument is deprecated',
    'core.tracklist.filter:kwargs_criteria':
        'tracklist.filter() with "kwargs" as criteria is deprecated',
    'core.tracklist.remove:kwargs_criteria':
        'tracklist.remove() with "kwargs" as criteria is deprecated',

    'core.tracklist.eot_track':
        'tracklist.eot_track() is pending deprecation, use '
        'tracklist.get_eot_tlid()',
    'core.tracklist.next_track':
        'tracklist.next_track() is pending deprecation, use '
        'tracklist.get_next_tlid()',
    'core.tracklist.previous_track':
        'tracklist.previous_track() is pending deprecation, use '
        'tracklist.get_previous_tlid()',

    'models.immutable.copy':
        'ImmutableObject.copy() is deprecated, use ImmutableObject.replace()',
}


def warn(msg_id, pending=False):
    if pending:
        category = PendingDeprecationWarning
    else:
        category = DeprecationWarning
    warnings.warn(_MESSAGES.get(msg_id, msg_id), category)


@contextlib.contextmanager
def ignore(ids=None):
    with warnings.catch_warnings():
        if isinstance(ids, compat.string_types):
            ids = [ids]

        if ids:
            for msg_id in ids:
                msg = re.escape(_MESSAGES.get(msg_id, msg_id))
                warnings.filterwarnings('ignore', msg, DeprecationWarning)
        else:
            warnings.filterwarnings('ignore', category=DeprecationWarning)
        yield


def deprecated_property(
        getter=None, setter=None, message='Property is deprecated'):

    # During development, this is a convenient place to add logging, emit
    # warnings, or ``assert False`` to ensure you are not using any of the
    # deprecated properties.
    #
    # Using inspect to find the call sites to emit proper warnings makes
    # parallel execution of our test suite slower than serial execution. Thus,
    # we don't want to add any extra overhead here by default.

    return property(getter, setter)
