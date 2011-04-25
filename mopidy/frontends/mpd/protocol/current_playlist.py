from mopidy.frontends.mpd.exceptions import (MpdArgError, MpdNoExistError,
    MpdNotImplemented)
from mopidy.frontends.mpd.protocol import handle_pattern
from mopidy.frontends.mpd.translator import tracks_to_mpd_format

@handle_pattern(r'^add "(?P<uri>[^"]*)"$')
def add(frontend, uri):
    """
    *musicpd.org, current playlist section:*

        ``add {URI}``

        Adds the file ``URI`` to the playlist (directories add recursively).
        ``URI`` can also be a single file.

    *Clarifications:*

    - ``add ""`` should add all tracks in the library to the current playlist.
    """
    if not uri:
        return
    for handler_prefix in frontend.backend.uri_handlers.get():
        if uri.startswith(handler_prefix):
            track = frontend.backend.library.lookup(uri).get()
            if track is not None:
                frontend.backend.current_playlist.add(track)
                return
    raise MpdNoExistError(
        u'directory or file not found', command=u'add')

@handle_pattern(r'^addid "(?P<uri>[^"]*)"( "(?P<songpos>\d+)")*$')
def addid(frontend, uri, songpos=None):
    """
    *musicpd.org, current playlist section:*

        ``addid {URI} [POSITION]``

        Adds a song to the playlist (non-recursive) and returns the song id.

        ``URI`` is always a single file or URL. For example::

            addid "foo.mp3"
            Id: 999
            OK

    *Clarifications:*

    - ``addid ""`` should return an error.
    """
    if not uri:
        raise MpdNoExistError(u'No such song', command=u'addid')
    if songpos is not None:
        songpos = int(songpos)
    track = frontend.backend.library.lookup(uri).get()
    if track is None:
        raise MpdNoExistError(u'No such song', command=u'addid')
    if songpos and songpos > len(
            frontend.backend.current_playlist.tracks.get()):
        raise MpdArgError(u'Bad song index', command=u'addid')
    cp_track = frontend.backend.current_playlist.add(track,
        at_position=songpos).get()
    return ('Id', cp_track[0])

@handle_pattern(r'^delete "(?P<start>\d+):(?P<end>\d+)*"$')
def delete_range(frontend, start, end=None):
    """
    *musicpd.org, current playlist section:*

        ``delete [{POS} | {START:END}]``

        Deletes a song from the playlist.
    """
    start = int(start)
    if end is not None:
        end = int(end)
    else:
        end = len(frontend.backend.current_playlist.tracks.get())
    cp_tracks = frontend.backend.current_playlist.cp_tracks.get()[start:end]
    if not cp_tracks:
        raise MpdArgError(u'Bad song index', command=u'delete')
    for (cpid, _) in cp_tracks:
        frontend.backend.current_playlist.remove(cpid=cpid)

@handle_pattern(r'^delete "(?P<songpos>\d+)"$')
def delete_songpos(frontend, songpos):
    """See :meth:`delete_range`"""
    try:
        songpos = int(songpos)
        (cpid, _) = frontend.backend.current_playlist.cp_tracks.get()[songpos]
        frontend.backend.current_playlist.remove(cpid=cpid)
    except IndexError:
        raise MpdArgError(u'Bad song index', command=u'delete')

@handle_pattern(r'^deleteid "(?P<cpid>\d+)"$')
def deleteid(frontend, cpid):
    """
    *musicpd.org, current playlist section:*

        ``deleteid {SONGID}``

        Deletes the song ``SONGID`` from the playlist
    """
    try:
        cpid = int(cpid)
        if frontend.backend.playback.current_cpid.get() == cpid:
            frontend.backend.playback.next()
        return frontend.backend.current_playlist.remove(cpid=cpid).get()
    except LookupError:
        raise MpdNoExistError(u'No such song', command=u'deleteid')

@handle_pattern(r'^clear$')
def clear(frontend):
    """
    *musicpd.org, current playlist section:*

        ``clear``

        Clears the current playlist.
    """
    frontend.backend.current_playlist.clear()

@handle_pattern(r'^move "(?P<start>\d+):(?P<end>\d+)*" "(?P<to>\d+)"$')
def move_range(frontend, start, to, end=None):
    """
    *musicpd.org, current playlist section:*

        ``move [{FROM} | {START:END}] {TO}``

        Moves the song at ``FROM`` or range of songs at ``START:END`` to
        ``TO`` in the playlist.
    """
    if end is None:
        end = len(frontend.backend.current_playlist.tracks.get())
    start = int(start)
    end = int(end)
    to = int(to)
    frontend.backend.current_playlist.move(start, end, to)

@handle_pattern(r'^move "(?P<songpos>\d+)" "(?P<to>\d+)"$')
def move_songpos(frontend, songpos, to):
    """See :meth:`move_range`."""
    songpos = int(songpos)
    to = int(to)
    frontend.backend.current_playlist.move(songpos, songpos + 1, to)

@handle_pattern(r'^moveid "(?P<cpid>\d+)" "(?P<to>\d+)"$')
def moveid(frontend, cpid, to):
    """
    *musicpd.org, current playlist section:*

        ``moveid {FROM} {TO}``

        Moves the song with ``FROM`` (songid) to ``TO`` (playlist index) in
        the playlist. If ``TO`` is negative, it is relative to the current
        song in the playlist (if there is one).
    """
    cpid = int(cpid)
    to = int(to)
    cp_track = frontend.backend.current_playlist.get(cpid=cpid).get()
    position = frontend.backend.current_playlist.cp_tracks.get().index(
        cp_track)
    frontend.backend.current_playlist.move(position, position + 1, to)

@handle_pattern(r'^playlist$')
def playlist(frontend):
    """
    *musicpd.org, current playlist section:*

        ``playlist``

        Displays the current playlist.

        .. note::

            Do not use this, instead use ``playlistinfo``.
    """
    return playlistinfo(frontend)

@handle_pattern(r'^playlistfind (?P<tag>[^"]+) "(?P<needle>[^"]+)"$')
@handle_pattern(r'^playlistfind "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
def playlistfind(frontend, tag, needle):
    """
    *musicpd.org, current playlist section:*

        ``playlistfind {TAG} {NEEDLE}``

        Finds songs in the current playlist with strict matching.

    *GMPC:*

    - does not add quotes around the tag.
    """
    if tag == 'filename':
        try:
            cp_track = frontend.backend.current_playlist.get(uri=needle).get()
            (cpid, track) = cp_track
            position = frontend.backend.current_playlist.cp_tracks.get().index(
                cp_track)
            return track.mpd_format(cpid=cpid, position=position)
        except LookupError:
            return None
    raise MpdNotImplemented # TODO

@handle_pattern(r'^playlistid( "(?P<cpid>\d+)")*$')
def playlistid(frontend, cpid=None):
    """
    *musicpd.org, current playlist section:*

        ``playlistid {SONGID}``

        Displays a list of songs in the playlist. ``SONGID`` is optional
        and specifies a single song to display info for.
    """
    if cpid is not None:
        try:
            cpid = int(cpid)
            cp_track = frontend.backend.current_playlist.get(cpid=cpid).get()
            position = frontend.backend.current_playlist.cp_tracks.get().index(
                cp_track)
            return cp_track[1].mpd_format(position=position, cpid=cpid)
        except LookupError:
            raise MpdNoExistError(u'No such song', command=u'playlistid')
    else:
        cpids = [ct[0] for ct in
            frontend.backend.current_playlist.cp_tracks.get()]
        return tracks_to_mpd_format(
            frontend.backend.current_playlist.tracks.get(), cpids=cpids)

@handle_pattern(r'^playlistinfo$')
@handle_pattern(r'^playlistinfo "(?P<songpos>-?\d+)"$')
@handle_pattern(r'^playlistinfo "(?P<start>\d+):(?P<end>\d+)*"$')
def playlistinfo(frontend, songpos=None,
        start=None, end=None):
    """
    *musicpd.org, current playlist section:*

        ``playlistinfo [[SONGPOS] | [START:END]]``

        Displays a list of all songs in the playlist, or if the optional
        argument is given, displays information only for the song
        ``SONGPOS`` or the range of songs ``START:END``.

    *ncmpc and mpc:*

    - uses negative indexes, like ``playlistinfo "-1"``, to request
      the entire playlist
    """
    if songpos == "-1":
        songpos = None

    if songpos is not None:
        songpos = int(songpos)
        start = songpos
        end = songpos + 1
        if start == -1:
            end = None
        cpids = [ct[0] for ct in
            frontend.backend.current_playlist.cp_tracks.get()]
        return tracks_to_mpd_format(
            frontend.backend.current_playlist.tracks.get(),
            start, end, cpids=cpids)
    else:
        if start is None:
            start = 0
        start = int(start)
        if not (0 <= start <= len(
                frontend.backend.current_playlist.tracks.get())):
            raise MpdArgError(u'Bad song index', command=u'playlistinfo')
        if end is not None:
            end = int(end)
            if end > len(frontend.backend.current_playlist.tracks.get()):
                end = None
        cpids = [ct[0] for ct in
            frontend.backend.current_playlist.cp_tracks.get()]
        return tracks_to_mpd_format(
            frontend.backend.current_playlist.tracks.get(),
            start, end, cpids=cpids)

@handle_pattern(r'^playlistsearch "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
@handle_pattern(r'^playlistsearch (?P<tag>\S+) "(?P<needle>[^"]+)"$')
def playlistsearch(frontend, tag, needle):
    """
    *musicpd.org, current playlist section:*

        ``playlistsearch {TAG} {NEEDLE}``

        Searches case-sensitively for partial matches in the current
        playlist.

    *GMPC:*

    - does not add quotes around the tag
    - uses ``filename`` and ``any`` as tags
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^plchanges (?P<version>-?\d+)$')
@handle_pattern(r'^plchanges "(?P<version>-?\d+)"$')
def plchanges(frontend, version):
    """
    *musicpd.org, current playlist section:*

        ``plchanges {VERSION}``

        Displays changed songs currently in the playlist since ``VERSION``.

        To detect songs that were deleted at the end of the playlist, use
        ``playlistlength`` returned by status command.

    *MPDroid:*

    - Calls ``plchanges "-1"`` two times per second to get the entire playlist.
    """
    # XXX Naive implementation that returns all tracks as changed
    if int(version) < frontend.backend.current_playlist.version:
        cpids = [ct[0] for ct in
            frontend.backend.current_playlist.cp_tracks.get()]
        return tracks_to_mpd_format(
            frontend.backend.current_playlist.tracks.get(), cpids=cpids)

@handle_pattern(r'^plchangesposid "(?P<version>\d+)"$')
def plchangesposid(frontend, version):
    """
    *musicpd.org, current playlist section:*

        ``plchangesposid {VERSION}``

        Displays changed songs currently in the playlist since ``VERSION``.
        This function only returns the position and the id of the changed
        song, not the complete metadata. This is more bandwidth efficient.

        To detect songs that were deleted at the end of the playlist, use
        ``playlistlength`` returned by status command.
    """
    # XXX Naive implementation that returns all tracks as changed
    if int(version) != frontend.backend.current_playlist.version.get():
        result = []
        for (position, (cpid, _)) in enumerate(
                frontend.backend.current_playlist.cp_tracks.get()):
            result.append((u'cpos', position))
            result.append((u'Id', cpid))
        return result

@handle_pattern(r'^shuffle$')
@handle_pattern(r'^shuffle "(?P<start>\d+):(?P<end>\d+)*"$')
def shuffle(frontend, start=None, end=None):
    """
    *musicpd.org, current playlist section:*

        ``shuffle [START:END]``

        Shuffles the current playlist. ``START:END`` is optional and
        specifies a range of songs.
    """
    if start is not None:
        start = int(start)
    if end is not None:
        end = int(end)
    frontend.backend.current_playlist.shuffle(start, end)

@handle_pattern(r'^swap "(?P<songpos1>\d+)" "(?P<songpos2>\d+)"$')
def swap(frontend, songpos1, songpos2):
    """
    *musicpd.org, current playlist section:*

        ``swap {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2``.
    """
    songpos1 = int(songpos1)
    songpos2 = int(songpos2)
    tracks = frontend.backend.current_playlist.tracks.get()
    song1 = tracks[songpos1]
    song2 = tracks[songpos2]
    del tracks[songpos1]
    tracks.insert(songpos1, song2)
    del tracks[songpos2]
    tracks.insert(songpos2, song1)
    frontend.backend.current_playlist.clear()
    frontend.backend.current_playlist.append(tracks)

@handle_pattern(r'^swapid "(?P<cpid1>\d+)" "(?P<cpid2>\d+)"$')
def swapid(frontend, cpid1, cpid2):
    """
    *musicpd.org, current playlist section:*

        ``swapid {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2`` (both song ids).
    """
    cpid1 = int(cpid1)
    cpid2 = int(cpid2)
    cp_track1 = frontend.backend.current_playlist.get(cpid=cpid1).get()
    cp_track2 = frontend.backend.current_playlist.get(cpid=cpid2).get()
    cp_tracks = frontend.backend.current_playlist.cp_tracks.get()
    position1 = cp_tracks.index(cp_track1)
    position2 = cp_tracks.index(cp_track2)
    swap(frontend, position1, position2)
