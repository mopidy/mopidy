import pykka.future

from mopidy.backends.base import PlaybackController
from mopidy.frontends.mpd.exceptions import MpdNotImplemented
from mopidy.frontends.mpd.protocol import handle_request
from mopidy.frontends.mpd.translator import track_to_mpd_format

#: Subsystems that can be registered with idle command.
SUBSYSTEMS = ['database', 'mixer', 'options', 'output',
    'player', 'playlist', 'stored_playlist', 'update', ]

@handle_request(r'^clearerror$')
def clearerror(context):
    """
    *musicpd.org, status section:*

        ``clearerror``

        Clears the current error message in status (this is also
        accomplished by any command that starts playback).
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^currentsong$')
def currentsong(context):
    """
    *musicpd.org, status section:*

        ``currentsong``

        Displays the song info of the current song (same song that is
        identified in status).
    """
    current_cp_track = context.backend.playback.current_cp_track.get()
    if current_cp_track is not None:
        position = context.backend.playback.current_playlist_position.get()
        return track_to_mpd_format(current_cp_track, position=position)

@handle_request(r'^idle$')
@handle_request(r'^idle (?P<subsystems>.+)$')
def idle(context, subsystems=None):
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

    if subsystems:
        subsystems = subsystems.split()
    else:
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
        response.append(u'changed: %s' % subsystem)
    return response

@handle_request(r'^noidle$')
def noidle(context):
    """See :meth:`_status_idle`."""
    if not context.subscriptions:
        return
    context.subscriptions = set()
    context.events = set()
    context.session.prevent_timeout = False

@handle_request(r'^stats$')
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
        'artists': 0, # TODO
        'albums': 0, # TODO
        'songs': 0, # TODO
        'uptime': 0, # TODO
        'db_playtime': 0, # TODO
        'db_update': 0, # TODO
        'playtime': 0, # TODO
    }

@handle_request(r'^status$')
def status(context):
    """
    *musicpd.org, status section:*

        ``status``

        Reports the current status of the player and the volume level.

        - ``volume``: 0-100
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
    futures = {
        'current_playlist.length': context.backend.current_playlist.length,
        'current_playlist.version': context.backend.current_playlist.version,
        'mixer.volume': context.mixer.volume,
        'playback.consume': context.backend.playback.consume,
        'playback.random': context.backend.playback.random,
        'playback.repeat': context.backend.playback.repeat,
        'playback.single': context.backend.playback.single,
        'playback.state': context.backend.playback.state,
        'playback.current_cp_track': context.backend.playback.current_cp_track,
        'playback.current_playlist_position':
            context.backend.playback.current_playlist_position,
        'playback.time_position': context.backend.playback.time_position,
    }
    pykka.future.get_all(futures.values())
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
    if futures['playback.current_cp_track'].get() is not None:
        result.append(('song', _status_songpos(futures)))
        result.append(('songid', _status_songid(futures)))
    if futures['playback.state'].get() in (PlaybackController.PLAYING,
            PlaybackController.PAUSED):
        result.append(('time', _status_time(futures)))
        result.append(('elapsed', _status_time_elapsed(futures)))
        result.append(('bitrate', _status_bitrate(futures)))
    return result

def _status_bitrate(futures):
    current_cp_track = futures['playback.current_cp_track'].get()
    if current_cp_track is not None:
        return current_cp_track.track.bitrate

def _status_consume(futures):
    if futures['playback.consume'].get():
        return 1
    else:
        return 0

def _status_playlist_length(futures):
    return futures['current_playlist.length'].get()

def _status_playlist_version(futures):
    return futures['current_playlist.version'].get()

def _status_random(futures):
    return int(futures['playback.random'].get())

def _status_repeat(futures):
    return int(futures['playback.repeat'].get())

def _status_single(futures):
    return int(futures['playback.single'].get())

def _status_songid(futures):
    current_cp_track = futures['playback.current_cp_track'].get()
    if current_cp_track is not None:
        return current_cp_track.cpid
    else:
        return _status_songpos(futures)

def _status_songpos(futures):
    return futures['playback.current_playlist_position'].get()

def _status_state(futures):
    state = futures['playback.state'].get()
    if state == PlaybackController.PLAYING:
        return u'play'
    elif state == PlaybackController.STOPPED:
        return u'stop'
    elif state == PlaybackController.PAUSED:
        return u'pause'

def _status_time(futures):
    return u'%d:%d' % (futures['playback.time_position'].get() // 1000,
        _status_time_total(futures) // 1000)

def _status_time_elapsed(futures):
    return u'%.3f' % (futures['playback.time_position'].get() / 1000.0)

def _status_time_total(futures):
    current_cp_track = futures['playback.current_cp_track'].get()
    if current_cp_track is None:
        return 0
    elif current_cp_track.track.length is None:
        return 0
    else:
        return current_cp_track.track.length

def _status_volume(futures):
    volume = futures['mixer.volume'].get()
    if volume is not None:
        return volume
    else:
        return 0

def _status_xfade(futures):
    return 0 # Not supported
