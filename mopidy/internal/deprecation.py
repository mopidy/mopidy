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

    # Deprecated features in core playback:
    'core.playback.play:tl_track_kwargs':
        'playback.play() with "tl_track" argument is pending deprecation use '
        '"tlid" instead',

    # Deprecated features in core tracklist:
    'core.tracklist.add:tracks_arg':
        'tracklist.add() "tracks" argument is deprecated',

    'core.tracklist.eot_track':
        'tracklist.eot_track() is pending deprecation, use '
        'tracklist.get_eot_tlid()',
    'core.tracklist.next_track':
        'tracklist.next_track() is pending deprecation, use '
        'tracklist.get_next_tlid()',
    'core.tracklist.previous_track':
        'tracklist.previous_track() is pending deprecation, use '
        'tracklist.get_previous_tlid()',
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
