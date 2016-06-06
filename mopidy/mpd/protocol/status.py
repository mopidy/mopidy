from __future__ import absolute_import, unicode_literals

import pykka

from mopidy.core import PlaybackState
from mopidy.mpd import exceptions, protocol, translator

#: Subsystems that can be registered with idle command.
SUBSYSTEMS = [
    'database', 'mixer', 'options', 'output', 'player', 'playlist',
    'stored_playlist', 'update']


@protocol.commands.add('clearerror')
def clearerror(context):
    """
    *musicpd.org, status section:*

        ``clearerror``

        Clears the current error message in status (this is also
        accomplished by any command that starts playback).
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('currentsong')
def currentsong(context):
    """
    *musicpd.org, status section:*

        ``currentsong``

        Displays the song info of the current song (same song that is
        identified in status).
    """
    tl_track = context.core.playback.get_current_tl_track().get()
    stream_title = context.core.playback.get_stream_title().get()
    if tl_track is not None:
        position = context.core.tracklist.index(tl_track).get()
        return translator.track_to_mpd_format(
            tl_track, position=position, stream_title=stream_title)


@protocol.commands.add('idle', list_command=False)
def idle(context, *subsystems):
    """
    *musicpd.org, status section:*

        ``idle [SUBSYSTEMS...]``

        Waits until there is a noteworthy change in one or more of MPD's
        subsystems. As soon as there is one, it lists all changed systems
        in a line in the format ``changed: SUBSYSTEM``, where ``SUBSYSTEM``
        is one of the following:

        - ``database``: the song database has been modified after update.
        - ``update``: a database update has started or finished. If the
          database was modified during the update, the database event is
          also emitted.
        - ``stored_playlist``: a stored playlist has been modified,
          renamed, created or deleted
        - ``playlist``: the current playlist has been modified
        - ``player``: the player has been started, stopped or seeked
        - ``mixer``: the volume has been changed
        - ``output``: an audio output has been enabled or disabled
        - ``options``: options like repeat, random, crossfade, replay gain

        While a client is waiting for idle results, the server disables
        timeouts, allowing a client to wait for events as long as MPD runs.
        The idle command can be canceled by sending the command ``noidle``
        (no other commands are allowed). MPD will then leave idle mode and
        print results immediately; might be empty at this time.

        If the optional ``SUBSYSTEMS`` argument is used, MPD will only send
        notifications when something changed in one of the specified
        subsystems.
    """
    # TODO: test against valid subsystems

    if not subsystems:
        subsystems = SUBSYSTEMS

    for subsystem in subsystems:
        context.subscriptions.add(subsystem)

    active = context.subscriptions.intersection(context.events)
    if not active:
        context.session.prevent_timeout = True
        return

    response = []
    context.events = set()
    context.subscriptions = set()

    for subsystem in active:
        response.append('changed: %s' % subsystem)
    return response


@protocol.commands.add('noidle', list_command=False)
def noidle(context):
    """See :meth:`_status_idle`."""
    if not context.subscriptions:
        return
    context.subscriptions = set()
    context.events = set()
    context.session.prevent_timeout = False


@protocol.commands.add('stats')
def stats(context):
    """
    *musicpd.org, status section:*

        ``stats``

        Displays statistics.

        - ``artists``: number of artists
        - ``songs``: number of albums
        - ``uptime``: daemon uptime in seconds
        - ``db_playtime``: sum of all song times in the db
        - ``db_update``: last db update in UNIX time
        - ``playtime``: time length of music played
    """
    return {
        'artists': 0,  # TODO
        'albums': 0,  # TODO
        'songs': 0,  # TODO
        'uptime': 0,  # TODO
        'db_playtime': 0,  # TODO
        'db_update': 0,  # TODO
        'playtime': 0,  # TODO
    }


@protocol.commands.add('status')
def status(context):
    """
    *musicpd.org, status section:*

        ``status``

        Reports the current status of the player and the volume level.

        - ``volume``: 0-100 or -1
        - ``repeat``: 0 or 1
        - ``single``: 0 or 1
        - ``consume``: 0 or 1
        - ``playlist``: 31-bit unsigned integer, the playlist version
          number
        - ``playlistlength``: integer, the length of the playlist
        - ``state``: play, stop, or pause
        - ``song``: playlist song number of the current song stopped on or
          playing
        - ``songid``: playlist songid of the current song stopped on or
          playing
        - ``nextsong``: playlist song number of the next song to be played
        - ``nextsongid``: playlist songid of the next song to be played
        - ``time``: total time elapsed (of current playing/paused song)
        - ``elapsed``: Total time elapsed within the current song, but with
          higher resolution.
        - ``bitrate``: instantaneous bitrate in kbps
        - ``xfade``: crossfade in seconds
        - ``audio``: sampleRate``:bits``:channels
        - ``updatings_db``: job id
        - ``error``: if there is an error, returns message here

    *Clarifications based on experience implementing*
        - ``volume``: can also be -1 if no output is set.
        - ``elapsed``: Higher resolution means time in seconds with three
          decimal places for millisecond precision.
    """
    tl_track = context.core.playback.get_current_tl_track()
    next_tlid = context.core.tracklist.get_next_tlid()

    futures = {
        'tracklist.length': context.core.tracklist.get_length(),
        'tracklist.version': context.core.tracklist.get_version(),
        'mixer.volume': context.core.mixer.get_volume(),
        'tracklist.consume': context.core.tracklist.get_consume(),
        'tracklist.random': context.core.tracklist.get_random(),
        'tracklist.repeat': context.core.tracklist.get_repeat(),
        'tracklist.single': context.core.tracklist.get_single(),
        'playback.state': context.core.playback.get_state(),
        'playback.current_tl_track': tl_track,
        'tracklist.index': context.core.tracklist.index(tl_track.get()),
        'tracklist.next_tlid': next_tlid,
        'tracklist.next_index': context.core.tracklist.index(
            tlid=next_tlid.get()),
        'playback.time_position': context.core.playback.get_time_position(),
    }
    pykka.get_all(futures.values())
    result = [
        ('volume', _status_volume(futures)),
        ('repeat', _status_repeat(futures)),
        ('random', _status_random(futures)),
        ('single', _status_single(futures)),
        ('consume', _status_consume(futures)),
        ('playlist', _status_playlist_version(futures)),
        ('playlistlength', _status_playlist_length(futures)),
        ('xfade', _status_xfade(futures)),
        ('state', _status_state(futures)),
    ]
    if futures['playback.current_tl_track'].get() is not None:
        result.append(('song', _status_songpos(futures)))
        result.append(('songid', _status_songid(futures)))
    if futures['tracklist.next_tlid'].get() is not None:
        result.append(('nextsong', _status_nextsongpos(futures)))
        result.append(('nextsongid', _status_nextsongid(futures)))
    if futures['playback.state'].get() in (
            PlaybackState.PLAYING, PlaybackState.PAUSED):
        result.append(('time', _status_time(futures)))
        result.append(('elapsed', _status_time_elapsed(futures)))
        result.append(('bitrate', _status_bitrate(futures)))
    return result


def _status_bitrate(futures):
    current_tl_track = futures['playback.current_tl_track'].get()
    if current_tl_track is None:
        return 0
    if current_tl_track.track.bitrate is None:
        return 0
    return current_tl_track.track.bitrate


def _status_consume(futures):
    if futures['tracklist.consume'].get():
        return 1
    else:
        return 0


def _status_playlist_length(futures):
    return futures['tracklist.length'].get()


def _status_playlist_version(futures):
    return futures['tracklist.version'].get()


def _status_random(futures):
    return int(futures['tracklist.random'].get())


def _status_repeat(futures):
    return int(futures['tracklist.repeat'].get())


def _status_single(futures):
    return int(futures['tracklist.single'].get())


def _status_songid(futures):
    current_tl_track = futures['playback.current_tl_track'].get()
    if current_tl_track is not None:
        return current_tl_track.tlid
    else:
        return _status_songpos(futures)


def _status_songpos(futures):
    return futures['tracklist.index'].get()


def _status_nextsongid(futures):
    return futures['tracklist.next_tlid'].get()


def _status_nextsongpos(futures):
    return futures['tracklist.next_index'].get()


def _status_state(futures):
    state = futures['playback.state'].get()
    if state == PlaybackState.PLAYING:
        return 'play'
    elif state == PlaybackState.STOPPED:
        return 'stop'
    elif state == PlaybackState.PAUSED:
        return 'pause'


def _status_time(futures):
    return '%d:%d' % (
        futures['playback.time_position'].get() // 1000,
        _status_time_total(futures) // 1000)


def _status_time_elapsed(futures):
    return '%.3f' % (futures['playback.time_position'].get() / 1000.0)


def _status_time_total(futures):
    current_tl_track = futures['playback.current_tl_track'].get()
    if current_tl_track is None:
        return 0
    elif current_tl_track.track.length is None:
        return 0
    else:
        return current_tl_track.track.length


def _status_volume(futures):
    volume = futures['mixer.volume'].get()
    if volume is not None:
        return volume
    else:
        return -1


def _status_xfade(futures):
    return 0  # Not supported
