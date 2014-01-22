from __future__ import unicode_literals

from mopidy.mpd import exceptions, protocol, translator


@protocol.commands.add('add')
def add(context, uri):
    """
    *musicpd.org, current playlist section:*

        ``add {URI}``

        Adds the file ``URI`` to the playlist (directories add recursively).
        ``URI`` can also be a single file.

    *Clarifications:*

    - ``add ""`` should add all tracks in the library to the current playlist.
    """
    if not uri.strip('/'):
        return

    tl_tracks = context.core.tracklist.add(uri=uri).get()
    if tl_tracks:
        return

    try:
        uri = context.directory_path_to_uri(translator.normalize_path(uri))
    except exceptions.MpdNoExistError as e:
        e.message = 'directory or file not found'
        raise

    browse_futures = [context.core.library.browse(uri)]
    lookup_futures = []
    while browse_futures:
        for ref in browse_futures.pop().get():
            if ref.type == ref.DIRECTORY:
                browse_futures.append(context.core.library.browse(ref.uri))
            else:
                lookup_futures.append(context.core.library.lookup(ref.uri))

    tracks = []
    for future in lookup_futures:
        tracks.extend(future.get())

    if not tracks:
        raise exceptions.MpdNoExistError('directory or file not found')

    context.core.tracklist.add(tracks=tracks)


@protocol.commands.add('addid', songpos=protocol.integer)
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
    # TODO: check that songpos is positive
    if not uri:
        raise exceptions.MpdNoExistError('No such song')
    if songpos is not None and songpos > context.core.tracklist.length.get():
        raise exceptions.MpdArgError('Bad song index')
    tl_tracks = context.core.tracklist.add(uri=uri, at_position=songpos).get()
    if not tl_tracks:
        raise exceptions.MpdNoExistError('No such song')
    return ('Id', tl_tracks[0].tlid)


@protocol.commands.add('delete', position=protocol.position_or_range)
def delete(context, position):
    """
    *musicpd.org, current playlist section:*

        ``delete [{POS} | {START:END}]``

        Deletes a song from the playlist.
    """
    start = position.start
    end = position.stop
    if end is None:
        end = context.core.tracklist.length.get()
    tl_tracks = context.core.tracklist.slice(start, end).get()
    if not tl_tracks:
        raise exceptions.MpdArgError('Bad song index', command='delete')
    for (tlid, _) in tl_tracks:
        context.core.tracklist.remove(tlid=[tlid])


@protocol.commands.add('deleteid', tlid=protocol.integer)
def deleteid(context, tlid):
    """
    *musicpd.org, current playlist section:*

        ``deleteid {SONGID}``

        Deletes the song ``SONGID`` from the playlist
    """
    # TODO: check that tlid is positive
    tl_tracks = context.core.tracklist.remove(tlid=[tlid]).get()
    if not tl_tracks:
        raise exceptions.MpdNoExistError('No such song')


@protocol.commands.add('clear')
def clear(context):
    """
    *musicpd.org, current playlist section:*

        ``clear``

        Clears the current playlist.
    """
    context.core.tracklist.clear()


@protocol.commands.add(
    'move', position=protocol.position_or_range, to=protocol.integer)
def move_range(context, position, to):
    """
    *musicpd.org, current playlist section:*

        ``move [{FROM} | {START:END}] {TO}``

        Moves the song at ``FROM`` or range of songs at ``START:END`` to
        ``TO`` in the playlist.
    """
    # TODO: check that to is positive
    start = position.start
    end = position.stop
    if end is None:
        end = context.core.tracklist.length.get()
    context.core.tracklist.move(start, end, to)


@protocol.commands.add('moveid', tlid=protocol.integer, to=protocol.integer)
def moveid(context, tlid, to):
    """
    *musicpd.org, current playlist section:*

        ``moveid {FROM} {TO}``

        Moves the song with ``FROM`` (songid) to ``TO`` (playlist index) in
        the playlist. If ``TO`` is negative, it is relative to the current
        song in the playlist (if there is one).
    """
    # TODO: check that tlid and to are positive
    tl_tracks = context.core.tracklist.filter(tlid=[tlid]).get()
    if not tl_tracks:
        raise exceptions.MpdNoExistError('No such song')
    position = context.core.tracklist.index(tl_tracks[0]).get()
    context.core.tracklist.move(position, position + 1, to)


@protocol.commands.add('playlist')
def playlist(context):
    """
    *musicpd.org, current playlist section:*

        ``playlist``

        Displays the current playlist.

        .. note::

            Do not use this, instead use ``playlistinfo``.
    """
    return playlistinfo(context)


@protocol.commands.add('playlistfind')
def playlistfind(context, tag, needle):
    """
    *musicpd.org, current playlist section:*

        ``playlistfind {TAG} {NEEDLE}``

        Finds songs in the current playlist with strict matching.

    *GMPC:*

    - does not add quotes around the tag.
    """
    if tag == 'filename':
        tl_tracks = context.core.tracklist.filter(uri=[needle]).get()
        if not tl_tracks:
            return None
        position = context.core.tracklist.index(tl_tracks[0]).get()
        return translator.track_to_mpd_format(tl_tracks[0], position=position)
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('playlistid', tlid=protocol.integer)
def playlistid(context, tlid=None):
    """
    *musicpd.org, current playlist section:*

        ``playlistid {SONGID}``

        Displays a list of songs in the playlist. ``SONGID`` is optional
        and specifies a single song to display info for.
    """
    # TODO: check that tlid is positive if not none
    if tlid is not None:
        tl_tracks = context.core.tracklist.filter(tlid=[tlid]).get()
        if not tl_tracks:
            raise exceptions.MpdNoExistError('No such song')
        position = context.core.tracklist.index(tl_tracks[0]).get()
        return translator.track_to_mpd_format(tl_tracks[0], position=position)
    else:
        return translator.tracks_to_mpd_format(
            context.core.tracklist.tl_tracks.get())


# TODO: convert
@protocol.handle_request(r'playlistinfo$')
@protocol.handle_request(r'playlistinfo\ "(?P<songpos>-?\d+)"$')
@protocol.handle_request(r'playlistinfo\ "(?P<start>\d+):(?P<end>\d+)*"$')
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
    if songpos == '-1':
        songpos = None
    if songpos is not None:
        songpos = int(songpos)
        tl_track = context.core.tracklist.tl_tracks.get()[songpos]
        return translator.track_to_mpd_format(tl_track, position=songpos)
    else:
        if start is None:
            start = 0
        start = int(start)
        if not (0 <= start <= context.core.tracklist.length.get()):
            raise exceptions.MpdArgError('Bad song index')
        if end is not None:
            end = int(end)
            if end > context.core.tracklist.length.get():
                end = None
        tl_tracks = context.core.tracklist.tl_tracks.get()
        return translator.tracks_to_mpd_format(tl_tracks, start, end)


@protocol.commands.add('playlistsearch')
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
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('plchanges', version=protocol.integer)
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


@protocol.commands.add('plchangesposid', version=protocol.integer)
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


@protocol.commands.add('shuffle', position=protocol.position_or_range)
def shuffle(context, position=None):
    """
    *musicpd.org, current playlist section:*

        ``shuffle [START:END]``

        Shuffles the current playlist. ``START:END`` is optional and
        specifies a range of songs.
    """
    if position is None:
        start, end = None, None
    else:
        start, end = position.start, position.stop
    context.core.tracklist.shuffle(start, end)


@protocol.commands.add(
    'swap', songpos1=protocol.integer, songpos2=protocol.integer)
def swap(context, songpos1, songpos2):
    """
    *musicpd.org, current playlist section:*

        ``swap {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2``.
    """
    # TODO: check that songpos is positive
    tracks = context.core.tracklist.tracks.get()
    song1 = tracks[songpos1]
    song2 = tracks[songpos2]
    del tracks[songpos1]
    tracks.insert(songpos1, song2)
    del tracks[songpos2]
    tracks.insert(songpos2, song1)
    context.core.tracklist.clear()
    context.core.tracklist.add(tracks)


@protocol.commands.add(
    'swapid', tlid1=protocol.integer, tlid2=protocol.integer)
def swapid(context, tlid1, tlid2):
    """
    *musicpd.org, current playlist section:*

        ``swapid {SONG1} {SONG2}``

        Swaps the positions of ``SONG1`` and ``SONG2`` (both song ids).
    """
    # TODO: check that tlid is positive
    tl_tracks1 = context.core.tracklist.filter(tlid=[tlid1]).get()
    tl_tracks2 = context.core.tracklist.filter(tlid=[tlid2]).get()
    if not tl_tracks1 or not tl_tracks2:
        raise exceptions.MpdNoExistError('No such song')
    position1 = context.core.tracklist.index(tl_tracks1[0]).get()
    position2 = context.core.tracklist.index(tl_tracks2[0]).get()
    swap(context, position1, position2)
