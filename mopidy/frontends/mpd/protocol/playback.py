from mopidy.backends.base import PlaybackController
from mopidy.frontends.mpd.protocol import handle_request
from mopidy.frontends.mpd.exceptions import (MpdArgError, MpdNoExistError,
    MpdNotImplemented)

@handle_request(r'^consume (?P<state>[01])$')
@handle_request(r'^consume "(?P<state>[01])"$')
def consume(context, state):
    """
    *musicpd.org, playback section:*

        ``consume {STATE}``

        Sets consume state to ``STATE``, ``STATE`` should be 0 or
        1. When consume is activated, each song played is removed from
        playlist.
    """
    if int(state):
        context.backend.playback.consume = True
    else:
        context.backend.playback.consume = False

@handle_request(r'^crossfade "(?P<seconds>\d+)"$')
def crossfade(context, seconds):
    """
    *musicpd.org, playback section:*

        ``crossfade {SECONDS}``

        Sets crossfading between songs.
    """
    seconds = int(seconds)
    raise MpdNotImplemented # TODO

@handle_request(r'^next$')
def next_(context):
    """
    *musicpd.org, playback section:*

        ``next``

        Plays next song in the playlist.

    *MPD's behaviour when affected by repeat/random/single/consume:*

        Given a playlist of three tracks numbered 1, 2, 3, and a currently
        playing track ``c``. ``next_track`` is defined at the track that
        will be played upon calls to ``next``.

        Tests performed on MPD 0.15.4-1ubuntu3.

        ======  ======  ======  =======  =====  =====  =====  =====
                    Inputs                    next_track
        -------------------------------  -------------------  -----
        repeat  random  single  consume  c = 1  c = 2  c = 3  Notes
        ======  ======  ======  =======  =====  =====  =====  =====
        T       T       T       T        2      3      EOPL
        T       T       T       .        Rand   Rand   Rand   [1]
        T       T       .       T        Rand   Rand   Rand   [4]
        T       T       .       .        Rand   Rand   Rand   [4]
        T       .       T       T        2      3      EOPL
        T       .       T       .        2      3      1
        T       .       .       T        3      3      EOPL
        T       .       .       .        2      3      1
        .       T       T       T        Rand   Rand   Rand   [3]
        .       T       T       .        Rand   Rand   Rand   [3]
        .       T       .       T        Rand   Rand   Rand   [2]
        .       T       .       .        Rand   Rand   Rand   [2]
        .       .       T       T        2      3      EOPL
        .       .       T       .        2      3      EOPL
        .       .       .       T        2      3      EOPL
        .       .       .       .        2      3      EOPL
        ======  ======  ======  =======  =====  =====  =====  =====

        - When end of playlist (EOPL) is reached, the current track is
          unset.
        - [1] When *random* and *single* is combined, ``next`` selects
          a track randomly at each invocation, and not just the next track
          in an internal prerandomized playlist.
        - [2] When *random* is active, ``next`` will skip through
          all tracks in the playlist in random order, and finally EOPL is
          reached.
        - [3] *single* has no effect in combination with *random*
          alone, or *random* and *consume*.
        - [4] When *random* and *repeat* is active, EOPL is never
          reached, but the playlist is played again, in the same random
          order as the first time.

    """
    return context.backend.playback.next().get()

@handle_request(r'^pause$')
@handle_request(r'^pause "(?P<state>[01])"$')
def pause(context, state=None):
    """
    *musicpd.org, playback section:*

        ``pause {PAUSE}``

        Toggles pause/resumes playing, ``PAUSE`` is 0 or 1.

    *MPDroid:*

    - Calls ``pause`` without any arguments to toogle pause.
    """
    if state is None:
        if (context.backend.playback.state.get() ==
                PlaybackController.PLAYING):
            context.backend.playback.pause()
        elif (context.backend.playback.state.get() ==
                PlaybackController.PAUSED):
            context.backend.playback.resume()
    elif int(state):
        context.backend.playback.pause()
    else:
        context.backend.playback.resume()

@handle_request(r'^play$')
def play(context):
    """
    The original MPD server resumes from the paused state on ``play``
    without arguments.
    """
    return context.backend.playback.play().get()

@handle_request(r'^playid "(?P<cpid>\d+)"$')
@handle_request(r'^playid "(?P<cpid>-1)"$')
def playid(context, cpid):
    """
    *musicpd.org, playback section:*

        ``playid [SONGID]``

        Begins playing the playlist at song ``SONGID``.

    *Clarifications:*

    - ``playid "-1"`` when playing is ignored.
    - ``playid "-1"`` when paused resumes playback.
    - ``playid "-1"`` when stopped with a current track starts playback at the
      current track.
    - ``playid "-1"`` when stopped without a current track, e.g. after playlist
      replacement, starts playback at the first track.
    """
    cpid = int(cpid)
    if cpid == -1:
        return _play_minus_one(context)
    try:
        cp_track = context.backend.current_playlist.get(cpid=cpid).get()
        return context.backend.playback.play(cp_track).get()
    except LookupError:
        raise MpdNoExistError(u'No such song', command=u'playid')

@handle_request(r'^play (?P<songpos>-?\d+)$')
@handle_request(r'^play "(?P<songpos>-?\d+)"$')
def playpos(context, songpos):
    """
    *musicpd.org, playback section:*

        ``play [SONGPOS]``

        Begins playing the playlist at song number ``SONGPOS``.

    *Clarifications:*

    - ``playid "-1"`` when playing is ignored.
    - ``playid "-1"`` when paused resumes playback.
    - ``playid "-1"`` when stopped with a current track starts playback at the
      current track.
    - ``playid "-1"`` when stopped without a current track, e.g. after playlist
      replacement, starts playback at the first track.

    *BitMPC:*

    - issues ``play 6`` without quotes around the argument.
    """
    songpos = int(songpos)
    if songpos == -1:
        return _play_minus_one(context)
    try:
        cp_track = context.backend.current_playlist.slice(
            songpos, songpos + 1).get()[0]
        return context.backend.playback.play(cp_track).get()
    except IndexError:
        raise MpdArgError(u'Bad song index', command=u'play')

def _play_minus_one(context):
    if (context.backend.playback.state.get() == PlaybackController.PLAYING):
        return # Nothing to do
    elif (context.backend.playback.state.get() == PlaybackController.PAUSED):
        return context.backend.playback.resume().get()
    elif context.backend.playback.current_cp_track.get() is not None:
        cp_track = context.backend.playback.current_cp_track.get()
        return context.backend.playback.play(cp_track).get()
    elif context.backend.current_playlist.slice(0, 1).get():
        cp_track = context.backend.current_playlist.slice(0, 1).get()[0]
        return context.backend.playback.play(cp_track).get()
    else:
        return # Fail silently

@handle_request(r'^previous$')
def previous(context):
    """
    *musicpd.org, playback section:*

        ``previous``

        Plays previous song in the playlist.

    *MPD's behaviour when affected by repeat/random/single/consume:*

        Given a playlist of three tracks numbered 1, 2, 3, and a currently
        playing track ``c``. ``previous_track`` is defined at the track
        that will be played upon ``previous`` calls.

        Tests performed on MPD 0.15.4-1ubuntu3.

        ======  ======  ======  =======  =====  =====  =====
                    Inputs                  previous_track
        -------------------------------  -------------------
        repeat  random  single  consume  c = 1  c = 2  c = 3
        ======  ======  ======  =======  =====  =====  =====
        T       T       T       T        Rand?  Rand?  Rand?
        T       T       T       .        3      1      2
        T       T       .       T        Rand?  Rand?  Rand?
        T       T       .       .        3      1      2
        T       .       T       T        3      1      2
        T       .       T       .        3      1      2
        T       .       .       T        3      1      2
        T       .       .       .        3      1      2
        .       T       T       T        c      c      c
        .       T       T       .        c      c      c
        .       T       .       T        c      c      c
        .       T       .       .        c      c      c
        .       .       T       T        1      1      2
        .       .       T       .        1      1      2
        .       .       .       T        1      1      2
        .       .       .       .        1      1      2
        ======  ======  ======  =======  =====  =====  =====

        - If :attr:`time_position` of the current track is 15s or more,
          ``previous`` should do a seek to time position 0.

    """
    return context.backend.playback.previous().get()

@handle_request(r'^random (?P<state>[01])$')
@handle_request(r'^random "(?P<state>[01])"$')
def random(context, state):
    """
    *musicpd.org, playback section:*

        ``random {STATE}``

        Sets random state to ``STATE``, ``STATE`` should be 0 or 1.
    """
    if int(state):
        context.backend.playback.random = True
    else:
        context.backend.playback.random = False

@handle_request(r'^repeat (?P<state>[01])$')
@handle_request(r'^repeat "(?P<state>[01])"$')
def repeat(context, state):
    """
    *musicpd.org, playback section:*

        ``repeat {STATE}``

        Sets repeat state to ``STATE``, ``STATE`` should be 0 or 1.
    """
    if int(state):
        context.backend.playback.repeat = True
    else:
        context.backend.playback.repeat = False

@handle_request(r'^replay_gain_mode "(?P<mode>(off|track|album))"$')
def replay_gain_mode(context, mode):
    """
    *musicpd.org, playback section:*

        ``replay_gain_mode {MODE}``

        Sets the replay gain mode. One of ``off``, ``track``, ``album``.

        Changing the mode during playback may take several seconds, because
        the new settings does not affect the buffered data.

        This command triggers the options idle event.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^replay_gain_status$')
def replay_gain_status(context):
    """
    *musicpd.org, playback section:*

        ``replay_gain_status``

        Prints replay gain options. Currently, only the variable
        ``replay_gain_mode`` is returned.
    """
    return u'off' # TODO

@handle_request(r'^seek (?P<songpos>\d+) (?P<seconds>\d+)$')
@handle_request(r'^seek "(?P<songpos>\d+)" "(?P<seconds>\d+)"$')
def seek(context, songpos, seconds):
    """
    *musicpd.org, playback section:*

        ``seek {SONGPOS} {TIME}``

        Seeks to the position ``TIME`` (in seconds) of entry ``SONGPOS`` in
        the playlist.

    *Droid MPD:*

    - issues ``seek 1 120`` without quotes around the arguments.
    """
    if context.backend.playback.current_playlist_position != songpos:
        playpos(context, songpos)
    context.backend.playback.seek(int(seconds) * 1000)

@handle_request(r'^seekid "(?P<cpid>\d+)" "(?P<seconds>\d+)"$')
def seekid(context, cpid, seconds):
    """
    *musicpd.org, playback section:*

        ``seekid {SONGID} {TIME}``

        Seeks to the position ``TIME`` (in seconds) of song ``SONGID``.
    """
    if context.backend.playback.current_cpid != cpid:
        playid(context, cpid)
    context.backend.playback.seek(int(seconds) * 1000)

@handle_request(r'^setvol (?P<volume>[-+]*\d+)$')
@handle_request(r'^setvol "(?P<volume>[-+]*\d+)"$')
def setvol(context, volume):
    """
    *musicpd.org, playback section:*

        ``setvol {VOL}``

        Sets volume to ``VOL``, the range of volume is 0-100.

    *Droid MPD:*

    - issues ``setvol 50`` without quotes around the argument.
    """
    volume = int(volume)
    if volume < 0:
        volume = 0
    if volume > 100:
        volume = 100
    context.mixer.volume = volume

@handle_request(r'^single (?P<state>[01])$')
@handle_request(r'^single "(?P<state>[01])"$')
def single(context, state):
    """
    *musicpd.org, playback section:*

        ``single {STATE}``

        Sets single state to ``STATE``, ``STATE`` should be 0 or 1. When
        single is activated, playback is stopped after current song, or
        song is repeated if the ``repeat`` mode is enabled.
    """
    if int(state):
        context.backend.playback.single = True
    else:
        context.backend.playback.single = False

@handle_request(r'^stop$')
def stop(context):
    """
    *musicpd.org, playback section:*

        ``stop``

        Stops playing.
    """
    context.backend.playback.stop()
