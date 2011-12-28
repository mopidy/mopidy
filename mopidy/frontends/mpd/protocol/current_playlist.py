from mopidy.frontends.mpd.exceptions import (MpdArgError, MpdNoExistError,
    MpdNotImplemented)
from mopidy.frontends.mpd.protocol import handle_request
from mopidy.frontends.mpd.translator import (track_to_mpd_format,
    tracks_to_mpd_format)

@handle_request(r'^add "(?P<uri>[^"]*)"$')
def add(context, uri):
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
    for uri_scheme in context.backend.uri_schemes.get():
        if uri.startswith(uri_scheme):
            track = context.backend.library.lookup(uri).get()
            if track is not None:
                context.backend.current_playlist.add(track)
                return
    raise MpdNoExistError(
        u'directory or file not found', command=u'add')

@handle_request(r'^addid "(?P<uri>[^"]*)"( "(?P<songpos>\d+)")*$')
def addid(context, uri, songpos=None):
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
    track = context.backend.library.lookup(uri).get()
    if track is None:
        raise MpdNoExistError(u'No such song', command=u'addid')
    if songpos and songpos > len(
            context.backend.current_playlist.tracks.get()):
        raise MpdArgError(u'Bad song index', command=u'addid')
    cp_track = context.backend.current_playlist.add(track,
        at_position=songpos).get()
    return ('Id', cp_track.cpid)

@handle_request(r'^delete "(?P<start>\d+):(?P<end>\d+)*"$')
def delete_range(context, start, end=None):
    """
    *musicpd.org, current playlist section:*

        ``delete [{POS} | {START:END}]``

        Deletes a song from the playlist.
    """
    start = int(start)
    if end is not None:
        end = int(end)
    else:
        end = context.backend.current_playlist.length.get()
    cp_tracks = context.backend.current_playlist.slice(start, end).get()
    if not cp_tracks:
        raise MpdArgError(u'Bad song index', command=u'delete')
    for (cpid, _) in cp_tracks:
        context.backend.current_playlist.remove(cpid=cpid)

@handle_request(r'^delete "(?P<songpos>\d+)"$')
def delete_songpos(context, songpos):
    """See :meth:`delete_range`"""
    try:
        songpos = int(songpos)
        (cpid, _) = context.backend.current_playlist.slice(
            songpos, songpos + 1).get()[0]
        context.backend.current_playlist.remove(cpid=cpid)
    except IndexError:
        raise MpdArgError(u'Bad song index', command=u'delete')

@handle_request(r'^deleteid "(?P<cpid>\d+)"$')
def deleteid(context, cpid):
    """
    *musicpd.org, current playlist section:*

        ``deleteid {SONGID}``

        Deletes the song ``SONGID`` from the playlist
    """
    try:
        cpid = int(cpid)
        if context.backend.playback.current_cpid.get() == cpid:
            context.backend.playback.next()
        return context.backend.current_playlist.remove(cpid=cpid).get()
    except LookupError:
        raise MpdNoExistError(u'No such song', command=u'deleteid')

@handle_request(r'^clear$')
def clear(context):
    """
    *musicpd.org, current playlist section:*

        ``clear``

        Clears the current playlist.
    """
    context.backend.current_playlist.clear()

@handle_request(r'^move "(?P<start>\d+):(?P<end>\d+)*" "(?P<to>\d+)"$')
def move_range(context, start, to, end=None):
    """
    *musicpd.org, current playlist section:*

        ``move [{FROM} | {START:END}] {TO}``

        Moves the song at ``FROM`` or range of songs at ``START:END`` to
        ``TO`` in the playlist.
    """
    if end is None:
        end = len(context.backend.current_playlist.tracks.get())
    start = int(start)
    end = int(end)
    to = int(to)
    context.backend.current_playlist.move(start, end, to)

@handle_request(r'^move "(?P<songpos>\d+)" "(?P<to>\d+)"$')
def move_songpos(context, songpos, to):
    """See :meth:`move_range`."""
    songpos = int(songpos)
    to = int(to)
    context.backend.current_playlist.move(songpos, songpos + 1, to)

@handle_request(r'^moveid "(?P<cpid>\d+)" "(?P<to>\d+)"$')
def moveid(context, cpid, to):
    """
    *musicpd.org, current playlist section:*

        ``moveid {FROM} {TO}``

        Moves the song with ``FROM`` (songid) to ``TO`` (playlist index) in
        the playlist. If ``TO`` is negative, it is relative to the current
        song in the playlist (if there is one).
    """
    cpid = int(cpid)
    to = int(to)
    cp_track = context.backend.current_playlist.get(cpid=cpid).get()
    position = context.backend.current_playlist.index(cp_track).get()
    context.backend.current_playlist.move(position, position + 1, to)

@handle_request(r'^playlist$')
def playlist(context):
    """
    *musicpd.org, current playlist section:*

        ``playlist``

        Displays the current playlist.

        .. note::

            Do not use this, instead use ``playlistinfo``.
    """
    return playlistinfo(context)

@handle_request(r'^playlistfind (?P<tag>[^"]+) "(?P<needle>[^"]+)"$')
@handle_request(r'^playlistfind "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
def playlistfind(context, tag, needle):
    """
    *musicpd.org, current playlist section:*

        ``playlistfind {TAG} {NEEDLE}``

        Finds songs in the current playlist with strict matching.

    *GMPC:*

    - does not add quotes around the tag.
    """
    if tag == 'filename':
        try:
            cp_track = context.backend.current_playlist.get(uri=needle).get()
            position = context.backend.current_playlist.index(cp_track).get()
            return track_to_mpd_format(cp_track, position=position)
        except LookupError:
            return None
    raise MpdNotImplemented # TODO

@handle_request(r'^playlistid( "(?P<cpid>\d+)")*$')
def playlistid(context, cpid=None):
    """
    *musicpd.org, current playlist section:*

        ``playlistid {SONGID}``

        Displays a list of songs in the playlist. ``SONGID`` is optional
        and specifies a single song to display info for.
    """
    if cpid is not None:
        try:
            cpid = int(cpid)
            cp_track = context.backend.current_playlist.get(cpid=cpid).get()
            position = context.backend.current_playlist.index(cp_track).get()
            return track_to_mpd_format(cp_track, position=position)
        except LookupError:
            raise MpdNoExistError(u'No such song', command=u'playlistid')
    else:
        return tracks_to_mpd_format(
            context.backend.current_playlist.cp_tracks.get())

@handle_request(r'^playlistinfo$')
@handle_request(r'^playlistinfo "-1"$')
@handle_request(r'^playlistinfo "(?P<songpos>-?\d+)"$')
@handle_request(r'^playlistinfo "(?P<start>\d+):(?P<end>\d+)*"$')
def playlistinfo(context, songpos=None,
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
    if songpos is not None:
        songpos = int(songpos)
        cp_track = context.backend.current_playlist.get(cpid=songpos).get()
        return track_to_mpd_format(cp_track, position=songpos)
    else:
        if start is None:
            start = 0
        start = int(start)
        if not (0 <= start <= context.backend.current_playlist.length.get()):
            raise MpdArgError(u'Bad song index', command=u'playlistinfo')
        if end is not None:
            end = int(end)
            if end > context.backend.current_playlist.length.get():
                end = None
        cp_tracks = context.backend.current_playlist.cp_tracks.get()
        return tracks_to_mpd_format(cp_tracks, start, end)

@handle_request(r'^playlistsearch "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
@handle_request(r'^playlistsearch (?P<tag>\S+) "(?P<needle>[^"]+)"$')
def playlistsearch(context, tag, needle):
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

@handle_request(r'^plchanges (?P<version>-?\d+)$')
@handle_request(r'^plchanges "(?P<version>-?\d+)"$')
def plchanges(context, version):
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
    if int(version) < context.backend.current_playlist.version:
        return tracks_to_mpd_format(
            context.backend.current_playlist.cp_tracks.get())

@handle_request(r'^plchangesposid "(?P<version>\d+)"$')
def plchangesposid(context, version):
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
    if int(version) != context.backend.current_playlist.version.get():
        result = []
        for (position, (cpid, _)) in enumerate(
                context.backend.current_playlist.cp_tracks.get()):
            result.append((u'cpos', position))
            result.append((u'Id', cpid))
        return result

@handle_request(r'^shuffle$')
@handle_request(r'^shuffle "(?P<start>\d+):(?P<end>\d+)*"$')
def shuffle(context, start=None, end=None):
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
    context.backend.current_playlist.shuffle(start, end)

@handle_request(r'^swap "(?P<songpos1>\d+)" "(?P<songpos2>\d+)"$')
def swap(context, songpos1, songpos2):
    """
    *musicpd.org, current playlist section:*

        ``swap {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2``.
    """
    songpos1 = int(songpos1)
    songpos2 = int(songpos2)
    tracks = context.backend.current_playlist.tracks.get()
    song1 = tracks[songpos1]
    song2 = tracks[songpos2]
    del tracks[songpos1]
    tracks.insert(songpos1, song2)
    del tracks[songpos2]
    tracks.insert(songpos2, song1)
    context.backend.current_playlist.clear()
    context.backend.current_playlist.append(tracks)

@handle_request(r'^swapid "(?P<cpid1>\d+)" "(?P<cpid2>\d+)"$')
def swapid(context, cpid1, cpid2):
    """
    *musicpd.org, current playlist section:*

        ``swapid {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2`` (both song ids).
    """
    cpid1 = int(cpid1)
    cpid2 = int(cpid2)
    cp_track1 = context.backend.current_playlist.get(cpid=cpid1).get()
    cp_track2 = context.backend.current_playlist.get(cpid=cpid2).get()
    position1 = context.backend.current_playlist.index(cp_track1).get()
    position2 = context.backend.current_playlist.index(cp_track2).get()
    swap(context, position1, position2)
