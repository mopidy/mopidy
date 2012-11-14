from __future__ import unicode_literals

from mopidy.frontends.mpd import translator
from mopidy.frontends.mpd.exceptions import (
    MpdArgError, MpdNoExistError, MpdNotImplemented)
from mopidy.frontends.mpd.protocol import handle_request


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
    track = context.core.library.lookup(uri).get()
    if track:
        context.core.tracklist.add(track)
        return
    raise MpdNoExistError('directory or file not found', command='add')


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
        raise MpdNoExistError('No such song', command='addid')
    if songpos is not None:
        songpos = int(songpos)
    track = context.core.library.lookup(uri).get()
    if track is None:
        raise MpdNoExistError('No such song', command='addid')
    if songpos and songpos > context.core.tracklist.length.get():
        raise MpdArgError('Bad song index', command='addid')
    tl_track = context.core.tracklist.add(track, at_position=songpos).get()
    return ('Id', tl_track.tlid)


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
        end = context.core.tracklist.length.get()
    tl_tracks = context.core.tracklist.slice(start, end).get()
    if not tl_tracks:
        raise MpdArgError('Bad song index', command='delete')
    for (tlid, _) in tl_tracks:
        context.core.tracklist.remove(tlid=tlid)


@handle_request(r'^delete "(?P<songpos>\d+)"$')
def delete_songpos(context, songpos):
    """See :meth:`delete_range`"""
    try:
        songpos = int(songpos)
        (tlid, _) = context.core.tracklist.slice(
            songpos, songpos + 1).get()[0]
        context.core.tracklist.remove(tlid=tlid)
    except IndexError:
        raise MpdArgError('Bad song index', command='delete')


@handle_request(r'^deleteid "(?P<tlid>\d+)"$')
def deleteid(context, tlid):
    """
    *musicpd.org, current playlist section:*

        ``deleteid {SONGID}``

        Deletes the song ``SONGID`` from the playlist
    """
    try:
        tlid = int(tlid)
        if context.core.playback.current_tlid.get() == tlid:
            context.core.playback.next()
        return context.core.tracklist.remove(tlid=tlid).get()
    except LookupError:
        raise MpdNoExistError('No such song', command='deleteid')


@handle_request(r'^clear$')
def clear(context):
    """
    *musicpd.org, current playlist section:*

        ``clear``

        Clears the current playlist.
    """
    context.core.tracklist.clear()


@handle_request(r'^move "(?P<start>\d+):(?P<end>\d+)*" "(?P<to>\d+)"$')
def move_range(context, start, to, end=None):
    """
    *musicpd.org, current playlist section:*

        ``move [{FROM} | {START:END}] {TO}``

        Moves the song at ``FROM`` or range of songs at ``START:END`` to
        ``TO`` in the playlist.
    """
    if end is None:
        end = context.core.tracklist.length.get()
    start = int(start)
    end = int(end)
    to = int(to)
    context.core.tracklist.move(start, end, to)


@handle_request(r'^move "(?P<songpos>\d+)" "(?P<to>\d+)"$')
def move_songpos(context, songpos, to):
    """See :meth:`move_range`."""
    songpos = int(songpos)
    to = int(to)
    context.core.tracklist.move(songpos, songpos + 1, to)


@handle_request(r'^moveid "(?P<tlid>\d+)" "(?P<to>\d+)"$')
def moveid(context, tlid, to):
    """
    *musicpd.org, current playlist section:*

        ``moveid {FROM} {TO}``

        Moves the song with ``FROM`` (songid) to ``TO`` (playlist index) in
        the playlist. If ``TO`` is negative, it is relative to the current
        song in the playlist (if there is one).
    """
    tlid = int(tlid)
    to = int(to)
    tl_track = context.core.tracklist.get(tlid=tlid).get()
    position = context.core.tracklist.index(tl_track).get()
    context.core.tracklist.move(position, position + 1, to)


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
            tl_track = context.core.tracklist.get(uri=needle).get()
            position = context.core.tracklist.index(tl_track).get()
            return translator.track_to_mpd_format(tl_track, position=position)
        except LookupError:
            return None
    raise MpdNotImplemented  # TODO


@handle_request(r'^playlistid( "(?P<tlid>\d+)")*$')
def playlistid(context, tlid=None):
    """
    *musicpd.org, current playlist section:*

        ``playlistid {SONGID}``

        Displays a list of songs in the playlist. ``SONGID`` is optional
        and specifies a single song to display info for.
    """
    if tlid is not None:
        try:
            tlid = int(tlid)
            tl_track = context.core.tracklist.get(tlid=tlid).get()
            position = context.core.tracklist.index(tl_track).get()
            return translator.track_to_mpd_format(tl_track, position=position)
        except LookupError:
            raise MpdNoExistError('No such song', command='playlistid')
    else:
        return translator.tracks_to_mpd_format(
            context.core.tracklist.tl_tracks.get())


@handle_request(r'^playlistinfo$')
@handle_request(r'^playlistinfo "-1"$')
@handle_request(r'^playlistinfo "(?P<songpos>-?\d+)"$')
@handle_request(r'^playlistinfo "(?P<start>\d+):(?P<end>\d+)*"$')
def playlistinfo(context, songpos=None, start=None, end=None):
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
        tl_track = context.core.tracklist.tl_tracks.get()[songpos]
        return translator.track_to_mpd_format(tl_track, position=songpos)
    else:
        if start is None:
            start = 0
        start = int(start)
        if not (0 <= start <= context.core.tracklist.length.get()):
            raise MpdArgError('Bad song index', command='playlistinfo')
        if end is not None:
            end = int(end)
            if end > context.core.tracklist.length.get():
                end = None
        tl_tracks = context.core.tracklist.tl_tracks.get()
        return translator.tracks_to_mpd_format(tl_tracks, start, end)


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
    raise MpdNotImplemented  # TODO


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
    if int(version) < context.core.tracklist.version.get():
        return translator.tracks_to_mpd_format(
            context.core.tracklist.tl_tracks.get())


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
    if int(version) != context.core.tracklist.version.get():
        result = []
        for (position, (tlid, _)) in enumerate(
                context.core.tracklist.tl_tracks.get()):
            result.append(('cpos', position))
            result.append(('Id', tlid))
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
    context.core.tracklist.shuffle(start, end)


@handle_request(r'^swap "(?P<songpos1>\d+)" "(?P<songpos2>\d+)"$')
def swap(context, songpos1, songpos2):
    """
    *musicpd.org, current playlist section:*

        ``swap {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2``.
    """
    songpos1 = int(songpos1)
    songpos2 = int(songpos2)
    tracks = context.core.tracklist.tracks.get()
    song1 = tracks[songpos1]
    song2 = tracks[songpos2]
    del tracks[songpos1]
    tracks.insert(songpos1, song2)
    del tracks[songpos2]
    tracks.insert(songpos2, song1)
    context.core.tracklist.clear()
    context.core.tracklist.append(tracks)


@handle_request(r'^swapid "(?P<tlid1>\d+)" "(?P<tlid2>\d+)"$')
def swapid(context, tlid1, tlid2):
    """
    *musicpd.org, current playlist section:*

        ``swapid {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2`` (both song ids).
    """
    tlid1 = int(tlid1)
    tlid2 = int(tlid2)
    tl_track1 = context.core.tracklist.get(tlid=tlid1).get()
    tl_track2 = context.core.tracklist.get(tlid=tlid2).get()
    position1 = context.core.tracklist.index(tl_track1).get()
    position2 = context.core.tracklist.index(tl_track2).get()
    swap(context, position1, position2)
