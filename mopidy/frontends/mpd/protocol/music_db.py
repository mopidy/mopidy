from __future__ import unicode_literals

import functools
import itertools

from mopidy.models import Track
from mopidy.frontends.mpd import translator
from mopidy.frontends.mpd.exceptions import MpdArgError, MpdNotImplemented
from mopidy.frontends.mpd.protocol import handle_request, stored_playlists


QUERY_RE = (
    r'(?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Aa]lbumartist|[Dd]ate|[Ff]ile|'
    r'[Ff]ilename|[Tt]itle|[Tt]rack|[Aa]ny)"? "[^"]*"\s?)+)$')


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


@handle_request(r'^count ' + QUERY_RE)
def count(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``count {TAG} {NEEDLE}``

        Counts the number of songs and their total playtime in the db
        matching ``TAG`` exactly.

    *GMPC:*

    - does not add quotes around the tag argument.
    - use multiple tag-needle pairs to make more specific searches.
    """
    try:
        query = translator.query_from_mpd_search_format(mpd_query)
    except ValueError:
        raise MpdArgError('incorrect arguments', command='count')
    results = context.core.library.find_exact(**query).get()
    result_tracks = _get_tracks(results)
    return [
        ('songs', len(result_tracks)),
        ('playtime', sum(track.length for track in result_tracks) / 1000),
    ]


@handle_request(r'^find ' + QUERY_RE)
def find(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``find {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT``. ``TYPE`` can be any
        tag supported by MPD, or one of the two special parameters - ``file``
        to search by full path (relative to database root), and ``any`` to
        match against all available tags. ``WHAT`` is what to find.

    *GMPC:*

    - does not add quotes around the field argument.
    - also uses ``find album "[ALBUM]" artist "[ARTIST]"`` to list album
      tracks.

    *ncmpc:*

    - does not add quotes around the field argument.
    - capitalizes the type argument.

    *ncmpcpp:*

    - also uses the search type "date".
    - uses "file" instead of "filename".
    """
    try:
        query = translator.query_from_mpd_search_format(mpd_query)
    except ValueError:
        return
    results = context.core.library.find_exact(**query).get()
    result_tracks = []
    if 'artist' not in query and 'albumartist' not in query:
        result_tracks += [_artist_as_track(a) for a in _get_artists(results)]
    if 'album' not in query:
        result_tracks += [_album_as_track(a) for a in _get_albums(results)]
    result_tracks += _get_tracks(results)
    return translator.tracks_to_mpd_format(result_tracks)


@handle_request(r'^findadd ' + QUERY_RE)
def findadd(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``findadd {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT`` and adds them to
        current playlist. Parameters have the same meaning as for ``find``.
    """
    try:
        query = translator.query_from_mpd_search_format(mpd_query)
    except ValueError:
        return
    results = context.core.library.find_exact(**query).get()
    context.core.tracklist.add(_get_tracks(results))


@handle_request(
    r'^list "?(?P<field>([Aa]rtist|[Aa]lbumartist|[Aa]lbum|[Dd]ate|'
    r'[Gg]enre))"?( (?P<mpd_query>.*))?$')
def list_(context, field, mpd_query=None):
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

    *GMPC:*

    - does not add quotes around the field argument.

    *ncmpc:*

    - does not add quotes around the field argument.
    - capitalizes the field argument.
    """
    field = field.lower()
    try:
        query = translator.query_from_mpd_list_format(field, mpd_query)
    except ValueError:
        return
    if field == 'artist':
        return _list_artist(context, query)
    if field == 'albumartist':
        return _list_albumartist(context, query)
    elif field == 'album':
        return _list_album(context, query)
    elif field == 'date':
        return _list_date(context, query)
    elif field == 'genre':
        pass  # TODO We don't have genre in our internal data structures yet


def _list_artist(context, query):
    artists = set()
    results = context.core.library.find_exact(**query).get()
    for track in _get_tracks(results):
        for artist in track.artists:
            if artist.name:
                artists.add(('Artist', artist.name))
    return artists


def _list_albumartist(context, query):
    albumartists = set()
    results = context.core.library.find_exact(**query).get()
    for track in _get_tracks(results):
        if track.album:
            for artist in track.album.artists:
                if artist.name:
                    albumartists.add(('AlbumArtist', artist.name))
    return albumartists


def _list_album(context, query):
    albums = set()
    results = context.core.library.find_exact(**query).get()
    for track in _get_tracks(results):
        if track.album and track.album.name:
            albums.add(('Album', track.album.name))
    return albums


def _list_date(context, query):
    dates = set()
    results = context.core.library.find_exact(**query).get()
    for track in _get_tracks(results):
        if track.date:
            dates.add(('Date', track.date))
    return dates


@handle_request(r'^listall$')
@handle_request(r'^listall "(?P<uri>[^"]+)"$')
def listall(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``listall [URI]``

        Lists all songs and directories in ``URI``.
    """
    raise MpdNotImplemented  # TODO


@handle_request(r'^listallinfo$')
@handle_request(r'^listallinfo "(?P<uri>[^"]+)"$')
def listallinfo(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``listallinfo [URI]``

        Same as ``listall``, except it also returns metadata info in the
        same format as ``lsinfo``.
    """
    raise MpdNotImplemented  # TODO


@handle_request(r'^lsinfo$')
@handle_request(r'^lsinfo "(?P<uri>[^"]*)"$')
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
    if uri is None or uri == '/' or uri == '':
        return stored_playlists.listplaylists(context)
    raise MpdNotImplemented  # TODO


@handle_request(r'^rescan( "(?P<uri>[^"]+)")*$')
def rescan(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``rescan [URI]``

        Same as ``update``, but also rescans unmodified files.
    """
    return update(context, uri, rescan_unmodified_files=True)


@handle_request(r'^search ' + QUERY_RE)
def search(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``search {TYPE} {WHAT} [...]``

        Searches for any song that contains ``WHAT``. Parameters have the same
        meaning as for ``find``, except that search is not case sensitive.

    *GMPC:*

    - does not add quotes around the field argument.
    - uses the undocumented field ``any``.
    - searches for multiple words like this::

        search any "foo" any "bar" any "baz"

    *ncmpc:*

    - does not add quotes around the field argument.
    - capitalizes the field argument.

    *ncmpcpp:*

    - also uses the search type "date".
    - uses "file" instead of "filename".
    """
    try:
        query = translator.query_from_mpd_search_format(mpd_query)
    except ValueError:
        return
    results = context.core.library.search(**query).get()
    artists = [_artist_as_track(a) for a in _get_artists(results)]
    albums = [_album_as_track(a) for a in _get_albums(results)]
    tracks = _get_tracks(results)
    return translator.tracks_to_mpd_format(artists + albums + tracks)


@handle_request(r'^searchadd ' + QUERY_RE)
def searchadd(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``searchadd {TYPE} {WHAT} [...]``

        Searches for any song that contains ``WHAT`` in tag ``TYPE`` and adds
        them to current playlist.

        Parameters have the same meaning as for ``find``, except that search is
        not case sensitive.
    """
    try:
        query = translator.query_from_mpd_search_format(mpd_query)
    except ValueError:
        return
    results = context.core.library.search(**query).get()
    context.core.tracklist.add(_get_tracks(results))


@handle_request(r'^searchaddpl "(?P<playlist_name>[^"]+)" ' + QUERY_RE)
def searchaddpl(context, playlist_name, mpd_query):
    """
    *musicpd.org, music database section:*

        ``searchaddpl {NAME} {TYPE} {WHAT} [...]``

        Searches for any song that contains ``WHAT`` in tag ``TYPE`` and adds
        them to the playlist named ``NAME``.

        If a playlist by that name doesn't exist it is created.

        Parameters have the same meaning as for ``find``, except that search is
        not case sensitive.
    """
    try:
        query = translator.query_from_mpd_search_format(mpd_query)
    except ValueError:
        return
    results = context.core.library.search(**query).get()

    playlist = context.lookup_playlist_from_name(playlist_name)
    if not playlist:
        playlist = context.core.playlists.create(playlist_name).get()
    tracks = list(playlist.tracks) + _get_tracks(results)
    playlist = playlist.copy(tracks=tracks)
    context.core.playlists.save(playlist)


@handle_request(r'^update( "(?P<uri>[^"]+)")*$')
def update(context, uri=None, rescan_unmodified_files=False):
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
