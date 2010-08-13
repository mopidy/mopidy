from mopidy.frontends.mpd import (handle_pattern, MpdArgError, MpdNoExistError,
    MpdNotImplemented)

@handle_pattern(r'^consume "(?P<state>[01])"$')
def consume(frontend, state):
    """
    *musicpd.org, playback section:*

        ``consume {STATE}``

        Sets consume state to ``STATE``, ``STATE`` should be 0 or
        1. When consume is activated, each song played is removed from
        playlist.
    """
    if int(state):
        frontend.backend.playback.consume = True
    else:
        frontend.backend.playback.consume = False

@handle_pattern(r'^crossfade "(?P<seconds>\d+)"$')
def crossfade(frontend, seconds):
    """
    *musicpd.org, playback section:*

        ``crossfade {SECONDS}``

        Sets crossfading between songs.
    """
    seconds = int(seconds)
    raise MpdNotImplemented # TODO

@handle_pattern(r'^next$')
def next_(frontend):
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
    return frontend.backend.playback.next()

@handle_pattern(r'^pause$')
@handle_pattern(r'^pause "(?P<state>[01])"$')
def pause(frontend, state=None):
    """
    *musicpd.org, playback section:*

        ``pause {PAUSE}``

        Toggles pause/resumes playing, ``PAUSE`` is 0 or 1.

    *MPDroid:*

    - Calls ``pause`` without any arguments to toogle pause.
    """
    if state is None:
        if (frontend.backend.playback.state ==
                frontend.backend.playback.PLAYING):
            frontend.backend.playback.pause()
        elif (frontend.backend.playback.state ==
                frontend.backend.playback.PAUSED):
            frontend.backend.playback.resume()
    elif int(state):
        frontend.backend.playback.pause()
    else:
        frontend.backend.playback.resume()

@handle_pattern(r'^play$')
def play(frontend):
    """
    The original MPD server resumes from the paused state on ``play``
    without arguments.
    """
    return frontend.backend.playback.play()

@handle_pattern(r'^playid "(?P<cpid>\d+)"$')
@handle_pattern(r'^playid "(?P<cpid>-1)"$')
def playid(frontend, cpid):
    """
    *musicpd.org, playback section:*

        ``playid [SONGID]``

        Begins playing the playlist at song ``SONGID``.

    *GMPC:*

    - issues ``playid "-1"`` after playlist replacement to start playback
      at the first track.
    """
    cpid = int(cpid)
    try:
        if cpid == -1:
            if not frontend.backend.current_playlist.cp_tracks:
                return # Fail silently
            cp_track = frontend.backend.current_playlist.cp_tracks[0]
        else:
            cp_track = frontend.backend.current_playlist.get(cpid=cpid)
        return frontend.backend.playback.play(cp_track)
    except LookupError:
        raise MpdNoExistError(u'No such song', command=u'playid')

@handle_pattern(r'^play "(?P<songpos>\d+)"$')
@handle_pattern(r'^play "(?P<songpos>-1)"$')
def playpos(frontend, songpos):
    """
    *musicpd.org, playback section:*

        ``play [SONGPOS]``

        Begins playing the playlist at song number ``SONGPOS``.

    *MPoD:*

    - issues ``play "-1"`` after playlist replacement to start playback at
      the first track.
    """
    songpos = int(songpos)
    try:
        if songpos == -1:
            if not frontend.backend.current_playlist.cp_tracks:
                return # Fail silently
            cp_track = frontend.backend.current_playlist.cp_tracks[0]
        else:
            cp_track = frontend.backend.current_playlist.cp_tracks[songpos]
        return frontend.backend.playback.play(cp_track)
    except IndexError:
        raise MpdArgError(u'Bad song index', command=u'play')

@handle_pattern(r'^previous$')
def previous(frontend):
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
    return frontend.backend.playback.previous()

@handle_pattern(r'^random "(?P<state>[01])"$')
def random(frontend, state):
    """
    *musicpd.org, playback section:*

        ``random {STATE}``

        Sets random state to ``STATE``, ``STATE`` should be 0 or 1.
    """
    if int(state):
        frontend.backend.playback.random = True
    else:
        frontend.backend.playback.random = False

@handle_pattern(r'^repeat "(?P<state>[01])"$')
def repeat(frontend, state):
    """
    *musicpd.org, playback section:*

        ``repeat {STATE}``

        Sets repeat state to ``STATE``, ``STATE`` should be 0 or 1.
    """
    if int(state):
        frontend.backend.playback.repeat = True
    else:
        frontend.backend.playback.repeat = False

@handle_pattern(r'^replay_gain_mode "(?P<mode>(off|track|album))"$')
def replay_gain_mode(frontend, mode):
    """
    *musicpd.org, playback section:*

        ``replay_gain_mode {MODE}``

        Sets the replay gain mode. One of ``off``, ``track``, ``album``.

        Changing the mode during playback may take several seconds, because
        the new settings does not affect the buffered data.

        This command triggers the options idle event.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^replay_gain_status$')
def replay_gain_status(frontend):
    """
    *musicpd.org, playback section:*

        ``replay_gain_status``

        Prints replay gain options. Currently, only the variable
        ``replay_gain_mode`` is returned.
    """
    return u'off' # TODO

@handle_pattern(r'^seek "(?P<songpos>\d+)" "(?P<seconds>\d+)"$')
def seek(frontend, songpos, seconds):
    """
    *musicpd.org, playback section:*

        ``seek {SONGPOS} {TIME}``

        Seeks to the position ``TIME`` (in seconds) of entry ``SONGPOS`` in
        the playlist.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^seekid "(?P<cpid>\d+)" "(?P<seconds>\d+)"$')
def seekid(frontend, cpid, seconds):
    """
    *musicpd.org, playback section:*

        ``seekid {SONGID} {TIME}``

        Seeks to the position ``TIME`` (in seconds) of song ``SONGID``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^setvol "(?P<volume>[-+]*\d+)"$')
def setvol(frontend, volume):
    """
    *musicpd.org, playback section:*

        ``setvol {VOL}``

        Sets volume to ``VOL``, the range of volume is 0-100.
    """
    volume = int(volume)
    if volume < 0:
        volume = 0
    if volume > 100:
        volume = 100
    frontend.backend.mixer.volume = volume

@handle_pattern(r'^single "(?P<state>[01])"$')
def single(frontend, state):
    """
    *musicpd.org, playback section:*

        ``single {STATE}``

        Sets single state to ``STATE``, ``STATE`` should be 0 or 1. When
        single is activated, playback is stopped after current song, or
        song is repeated if the ``repeat`` mode is enabled.
    """
    if int(state):
        frontend.backend.playback.single = True
    else:
        frontend.backend.playback.single = False

@handle_pattern(r'^stop$')
def stop(frontend):
    """
    *musicpd.org, playback section:*

        ``stop``

        Stops playing.
    """
    frontend.backend.playback.stop()
