from __future__ import absolute_import, unicode_literals

import functools
import itertools

from mopidy.internal import deprecation
from mopidy.models import Track
from mopidy.mpd import exceptions, protocol, translator

_SEARCH_MAPPING = {
    'album': 'album',
    'albumartist': 'albumartist',
    'any': 'any',
    'artist': 'artist',
    'comment': 'comment',
    'composer': 'composer',
    'date': 'date',
    'file': 'uri',
    'filename': 'uri',
    'genre': 'genre',
    'performer': 'performer',
    'title': 'track_name',
    'track': 'track_no'}

_LIST_MAPPING = {
    'title': 'track',
    'album': 'album',
    'albumartist': 'albumartist',
    'artist': 'artist',
    'composer': 'composer',
    'date': 'date',
    'genre': 'genre',
    'performer': 'performer'}

_LIST_NAME_MAPPING = {
    'track': 'Title',
    'album': 'Album',
    'albumartist': 'AlbumArtist',
    'artist': 'Artist',
    'composer': 'Composer',
    'date': 'Date',
    'genre': 'Genre',
    'performer': 'Performer'}


def _query_from_mpd_search_parameters(parameters, mapping):
    query = {}
    parameters = list(parameters)
    while parameters:
        # TODO: does it matter that this is now case insensitive
        field = mapping.get(parameters.pop(0).lower())
        if not field:
            raise exceptions.MpdArgError('incorrect arguments')
        if not parameters:
            raise ValueError
        value = parameters.pop(0)
        if value.strip():
            query.setdefault(field, []).append(value)
    return query


def _get_field(field, search_results):
    return list(itertools.chain(*[getattr(r, field) for r in search_results]))


_get_albums = functools.partial(_get_field, 'albums')
_get_artists = functools.partial(_get_field, 'artists')
_get_tracks = functools.partial(_get_field, 'tracks')


def _album_as_track(album):
    return Track(
        uri=album.uri,
        name='Album: ' + album.name,
        artists=album.artists,
        album=album,
        date=album.date)


def _artist_as_track(artist):
    return Track(
        uri=artist.uri,
        name='Artist: ' + artist.name,
        artists=[artist])


@protocol.commands.add('count')
def count(context, *args):
    """
    *musicpd.org, music database section:*

        ``count {TAG} {NEEDLE}``

        Counts the number of songs and their total playtime in the db
        matching ``TAG`` exactly.

    *GMPC:*

    - use multiple tag-needle pairs to make more specific searches.
    """
    try:
        query = _query_from_mpd_search_parameters(args, _SEARCH_MAPPING)
    except ValueError:
        raise exceptions.MpdArgError('incorrect arguments')
    results = context.core.library.search(query=query, exact=True).get()
    result_tracks = _get_tracks(results)
    return [
        ('songs', len(result_tracks)),
        ('playtime', sum(t.length for t in result_tracks if t.length) / 1000),
    ]


@protocol.commands.add('find')
def find(context, *args):
    """
    *musicpd.org, music database section:*

        ``find {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT``. ``TYPE`` can be any
        tag supported by MPD, or one of the two special parameters - ``file``
        to search by full path (relative to database root), and ``any`` to
        match against all available tags. ``WHAT`` is what to find.

    *GMPC:*

    - also uses ``find album "[ALBUM]" artist "[ARTIST]"`` to list album
      tracks.

    *ncmpc:*

    - capitalizes the type argument.

    *ncmpcpp:*

    - also uses the search type "date".
    - uses "file" instead of "filename".
    """
    try:
        query = _query_from_mpd_search_parameters(args, _SEARCH_MAPPING)
    except ValueError:
        return

    with deprecation.ignore('core.library.search:empty_query'):
        results = context.core.library.search(query=query, exact=True).get()
    result_tracks = []
    if ('artist' not in query and
            'albumartist' not in query and
            'composer' not in query and
            'performer' not in query):
        result_tracks += [_artist_as_track(a) for a in _get_artists(results)]
    if 'album' not in query:
        result_tracks += [_album_as_track(a) for a in _get_albums(results)]
    result_tracks += _get_tracks(results)
    return translator.tracks_to_mpd_format(result_tracks)


@protocol.commands.add('findadd')
def findadd(context, *args):
    """
    *musicpd.org, music database section:*

        ``findadd {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT`` and adds them to
        current playlist. Parameters have the same meaning as for ``find``.
    """
    try:
        query = _query_from_mpd_search_parameters(args, _SEARCH_MAPPING)
    except ValueError:
        return

    results = context.core.library.search(query=query, exact=True).get()

    with deprecation.ignore('core.tracklist.add:tracks_arg'):
        # TODO: for now just use tracks as other wise we have to lookup the
        # tracks we just got from the search.
        context.core.tracklist.add(tracks=_get_tracks(results)).get()


@protocol.commands.add('list')
def list_(context, *args):
    """
    *musicpd.org, music database section:*

        ``list {TYPE} [ARTIST]``

        Lists all tags of the specified type. ``TYPE`` should be ``album``,
        ``artist``, ``albumartist``, ``date``, or ``genre``.

        ``ARTIST`` is an optional parameter when type is ``album``,
        ``date``, or ``genre``. This filters the result list by an artist.

    *Clarifications:*

        The musicpd.org documentation for ``list`` is far from complete. The
        command also supports the following variant:

        ``list {TYPE} {QUERY}``

        Where ``QUERY`` applies to all ``TYPE``. ``QUERY`` is one or more pairs
        of a field name and a value. If the ``QUERY`` consists of more than one
        pair, the pairs are AND-ed together to find the result. Examples of
        valid queries and what they should return:

        ``list "artist" "artist" "ABBA"``
            List artists where the artist name is "ABBA". Response::

                Artist: ABBA
                OK

        ``list "album" "artist" "ABBA"``
            Lists albums where the artist name is "ABBA". Response::

                Album: More ABBA Gold: More ABBA Hits
                Album: Absolute More Christmas
                Album: Gold: Greatest Hits
                OK

        ``list "artist" "album" "Gold: Greatest Hits"``
            Lists artists where the album name is "Gold: Greatest Hits".
            Response::

                Artist: ABBA
                OK

        ``list "artist" "artist" "ABBA" "artist" "TLC"``
            Lists artists where the artist name is "ABBA" *and* "TLC". Should
            never match anything. Response::

                OK

        ``list "date" "artist" "ABBA"``
            Lists dates where artist name is "ABBA". Response::

                Date:
                Date: 1992
                Date: 1993
                OK

        ``list "date" "artist" "ABBA" "album" "Gold: Greatest Hits"``
            Lists dates where artist name is "ABBA" and album name is "Gold:
            Greatest Hits". Response::

                Date: 1992
                OK

        ``list "genre" "artist" "The Rolling Stones"``
            Lists genres where artist name is "The Rolling Stones". Response::

                Genre:
                Genre: Rock
                OK

    *ncmpc:*

    - capitalizes the field argument.
    """
    params = list(args)
    if not params:
        raise exceptions.MpdArgError('incorrect arguments')

    field = params.pop(0).lower()
    field = _LIST_MAPPING.get(field)
    if field is None:
        raise exceptions.MpdArgError('incorrect arguments')

    query = None
    if len(params) == 1:
        if field != 'album':
            raise exceptions.MpdArgError('should be "Album" for 3 arguments')
        if params[0].strip():
            query = {'artist': params}
    else:
        try:
            query = _query_from_mpd_search_parameters(params, _LIST_MAPPING)
        except exceptions.MpdArgError as e:
            e.message = 'not able to parse args'
            raise
        except ValueError:
            return

    name = _LIST_NAME_MAPPING[field]
    result = context.core.library.get_distinct(field, query)
    return [(name, value) for value in result.get()]


@protocol.commands.add('listall')
def listall(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``listall [URI]``

        Lists all songs and directories in ``URI``.

        Do not use this command. Do not manage a client-side copy of MPD's
        database. That is fragile and adds huge overhead. It will break with
        large databases. Instead, query MPD whenever you need something.


    .. warning:: This command is disabled by default in Mopidy installs.
    """
    result = []
    for path, track_ref in context.browse(uri, lookup=False):
        if not track_ref:
            result.append(('directory', path))
        else:
            result.append(('file', track_ref.uri))

    if not result:
        raise exceptions.MpdNoExistError('Not found')
    return result


@protocol.commands.add('listallinfo')
def listallinfo(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``listallinfo [URI]``

        Same as ``listall``, except it also returns metadata info in the
        same format as ``lsinfo``.

        Do not use this command. Do not manage a client-side copy of MPD's
        database. That is fragile and adds huge overhead. It will break with
        large databases. Instead, query MPD whenever you need something.


    .. warning:: This command is disabled by default in Mopidy installs.
    """
    result = []
    for path, lookup_future in context.browse(uri):
        if not lookup_future:
            result.append(('directory', path))
        else:
            for tracks in lookup_future.get().values():
                for track in tracks:
                    result.extend(translator.track_to_mpd_format(track))
    return result


@protocol.commands.add('listfiles')
def listfiles(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``listfiles [URI]``

        Lists the contents of the directory URI, including files are not
        recognized by MPD. URI can be a path relative to the music directory or
        an URI understood by one of the storage plugins. The response contains
        at least one line for each directory entry with the prefix "file: " or
        "directory: ", and may be followed by file attributes such as
        "Last-Modified" and "size".

        For example, "smb://SERVER" returns a list of all shares on the given
        SMB/CIFS server; "nfs://servername/path" obtains a directory listing
        from the NFS server.

    .. versionadded:: 0.19
        New in MPD protocol version 0.19
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('lsinfo')
def lsinfo(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``lsinfo [URI]``

        Lists the contents of the directory ``URI``.

        When listing the root directory, this currently returns the list of
        stored playlists. This behavior is deprecated; use
        ``listplaylists`` instead.

    MPD returns the same result, including both playlists and the files and
    directories located at the root level, for both ``lsinfo``, ``lsinfo
    ""``, and ``lsinfo "/"``.
    """
    result = []
    for path, lookup_future in context.browse(uri, recursive=False):
        if not lookup_future:
            result.append(('directory', path.lstrip('/')))
        else:
            for tracks in lookup_future.get().values():
                if tracks:
                    result.extend(translator.track_to_mpd_format(tracks[0]))

    if uri in (None, '', '/'):
        result.extend(protocol.stored_playlists.listplaylists(context))

    return result


@protocol.commands.add('rescan')
def rescan(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``rescan [URI]``

        Same as ``update``, but also rescans unmodified files.
    """
    return {'updating_db': 0}  # TODO


@protocol.commands.add('search')
def search(context, *args):
    """
    *musicpd.org, music database section:*

        ``search {TYPE} {WHAT} [...]``

        Searches for any song that contains ``WHAT``. Parameters have the same
        meaning as for ``find``, except that search is not case sensitive.

    *GMPC:*

    - uses the undocumented field ``any``.
    - searches for multiple words like this::

        search any "foo" any "bar" any "baz"

    *ncmpc:*

    - capitalizes the field argument.

    *ncmpcpp:*

    - also uses the search type "date".
    - uses "file" instead of "filename".
    """
    try:
        query = _query_from_mpd_search_parameters(args, _SEARCH_MAPPING)
    except ValueError:
        return
    with deprecation.ignore('core.library.search:empty_query'):
        results = context.core.library.search(query).get()
    artists = [_artist_as_track(a) for a in _get_artists(results)]
    albums = [_album_as_track(a) for a in _get_albums(results)]
    tracks = _get_tracks(results)
    return translator.tracks_to_mpd_format(artists + albums + tracks)


@protocol.commands.add('searchadd')
def searchadd(context, *args):
    """
    *musicpd.org, music database section:*

        ``searchadd {TYPE} {WHAT} [...]``

        Searches for any song that contains ``WHAT`` in tag ``TYPE`` and adds
        them to current playlist.

        Parameters have the same meaning as for ``find``, except that search is
        not case sensitive.
    """
    try:
        query = _query_from_mpd_search_parameters(args, _SEARCH_MAPPING)
    except ValueError:
        return

    results = context.core.library.search(query).get()

    with deprecation.ignore('core.tracklist.add:tracks_arg'):
        # TODO: for now just use tracks as other wise we have to lookup the
        # tracks we just got from the search.
        context.core.tracklist.add(_get_tracks(results)).get()


@protocol.commands.add('searchaddpl')
def searchaddpl(context, *args):
    """
    *musicpd.org, music database section:*

        ``searchaddpl {NAME} {TYPE} {WHAT} [...]``

        Searches for any song that contains ``WHAT`` in tag ``TYPE`` and adds
        them to the playlist named ``NAME``.

        If a playlist by that name doesn't exist it is created.

        Parameters have the same meaning as for ``find``, except that search is
        not case sensitive.
    """
    parameters = list(args)
    if not parameters:
        raise exceptions.MpdArgError('incorrect arguments')
    playlist_name = parameters.pop(0)
    try:
        query = _query_from_mpd_search_parameters(parameters, _SEARCH_MAPPING)
    except ValueError:
        return
    results = context.core.library.search(query).get()

    uri = context.lookup_playlist_uri_from_name(playlist_name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        playlist = context.core.playlists.create(playlist_name).get()
    tracks = list(playlist.tracks) + _get_tracks(results)
    playlist = playlist.replace(tracks=tracks)
    context.core.playlists.save(playlist)


@protocol.commands.add('update')
def update(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``update [URI]``

        Updates the music database: find new files, remove deleted files,
        update modified files.

        ``URI`` is a particular directory or song/file to update. If you do
        not specify it, everything is updated.

        Prints ``updating_db: JOBID`` where ``JOBID`` is a positive number
        identifying the update job. You can read the current job id in the
        ``status`` response.
    """
    return {'updating_db': 0}  # TODO


# TODO: add at least reflection tests before adding NotImplemented version
# @protocol.commands.add('readcomments')
def readcomments(context, uri):
    """
    *musicpd.org, music database section:*

        ``readcomments [URI]``

        Read "comments" (i.e. key-value pairs) from the file specified by
        "URI". This "URI" can be a path relative to the music directory or a
        URL in the form "file:///foo/bar.ogg".

        This command may be used to list metadata of remote files (e.g. URI
        beginning with "http://" or "smb://").

        The response consists of lines in the form "KEY: VALUE". Comments with
        suspicious characters (e.g. newlines) are ignored silently.

        The meaning of these depends on the codec, and not all decoder plugins
        support it. For example, on Ogg files, this lists the Vorbis comments.
    """
    pass
