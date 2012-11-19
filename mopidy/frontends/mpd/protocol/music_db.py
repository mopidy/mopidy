from __future__ import unicode_literals

import re
import shlex

from mopidy.frontends.mpd.exceptions import MpdArgError, MpdNotImplemented
from mopidy.frontends.mpd.protocol import handle_request, stored_playlists
from mopidy.frontends.mpd.translator import tracks_to_mpd_format


def _build_query(mpd_query):
    """
    Parses a MPD query string and converts it to the Mopidy query format.
    """
    query_pattern = (
        r'"?(?:[Aa]lbum|[Aa]rtist|[Ff]ile[name]*|[Tt]itle|[Aa]ny)"? "[^"]+"')
    query_parts = re.findall(query_pattern, mpd_query)
    query_part_pattern = (
        r'"?(?P<field>([Aa]lbum|[Aa]rtist|[Ff]ile[name]*|[Tt]itle|[Aa]ny))"? '
        r'"(?P<what>[^"]+)"')
    query = {}
    for query_part in query_parts:
        m = re.match(query_part_pattern, query_part)
        field = m.groupdict()['field'].lower()
        if field == 'title':
            field = 'track'
        elif field in ('file', 'filename'):
            field = 'uri'
        field = str(field)  # Needed for kwargs keys on OS X and Windows
        what = m.groupdict()['what']
        if not what:
            raise ValueError
        if field in query:
            query[field].append(what)
        else:
            query[field] = [what]
    return query


@handle_request(r'^count "(?P<tag>[^"]+)" "(?P<needle>[^"]*)"$')
def count(context, tag, needle):
    """
    *musicpd.org, music database section:*

        ``count {TAG} {NEEDLE}``

        Counts the number of songs and their total playtime in the db
        matching ``TAG`` exactly.
    """
    return [('songs', 0), ('playtime', 0)]  # TODO


@handle_request(
    r'^find (?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Dd]ate|[Ff]ile[name]*|'
    r'[Tt]itle|[Aa]ny)"? "[^"]*"\s?)+)$')
def find(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``find {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT``. ``TYPE`` should be
        ``album``, ``artist``, or ``title``. ``WHAT`` is what to find.

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
        query = _build_query(mpd_query)
    except ValueError:
        return
    return tracks_to_mpd_format(
        context.core.library.find_exact(**query).get())


@handle_request(
    r'^findadd '
    r'(?P<query>("?([Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny)"? '
    r'"[^"]+"\s?)+)$')
def findadd(context, query):
    """
    *musicpd.org, music database section:*

        ``findadd {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT`` and adds them to
        current playlist. ``TYPE`` can be any tag supported by MPD.
        ``WHAT`` is what to find.
    """
    # TODO Add result to current playlist
    #result = context.find(query)


@handle_request(
    r'^list "?(?P<field>([Aa]rtist|[Aa]lbum|[Dd]ate|[Gg]enre))"?'
    r'( (?P<mpd_query>.*))?$')
def list_(context, field, mpd_query=None):
    """
    *musicpd.org, music database section:*

        ``list {TYPE} [ARTIST]``

        Lists all tags of the specified type. ``TYPE`` should be ``album``,
        ``artist``, ``date``, or ``genre``.

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
        query = _list_build_query(field, mpd_query)
    except ValueError:
        return
    if field == 'artist':
        return _list_artist(context, query)
    elif field == 'album':
        return _list_album(context, query)
    elif field == 'date':
        return _list_date(context, query)
    elif field == 'genre':
        pass  # TODO We don't have genre in our internal data structures yet


def _list_build_query(field, mpd_query):
    """Converts a ``list`` query to a Mopidy query."""
    if mpd_query is None:
        return {}
    try:
        # shlex does not seem to be friends with unicode objects
        tokens = shlex.split(mpd_query.encode('utf-8'))
    except ValueError as error:
        if str(error) == 'No closing quotation':
            raise MpdArgError('Invalid unquoted character', command='list')
        else:
            raise
    tokens = [t.decode('utf-8') for t in tokens]
    if len(tokens) == 1:
        if field == 'album':
            if not tokens[0]:
                raise ValueError
            return {'artist': [tokens[0]]}
        else:
            raise MpdArgError(
                'should be "Album" for 3 arguments', command='list')
    elif len(tokens) % 2 == 0:
        query = {}
        while tokens:
            key = tokens[0].lower()
            key = str(key)  # Needed for kwargs keys on OS X and Windows
            value = tokens[1]
            tokens = tokens[2:]
            if key not in ('artist', 'album', 'date', 'genre'):
                raise MpdArgError('not able to parse args', command='list')
            if not value:
                raise ValueError
            if key in query:
                query[key].append(value)
            else:
                query[key] = [value]
        return query
    else:
        raise MpdArgError('not able to parse args', command='list')


def _list_artist(context, query):
    artists = set()
    tracks = context.core.library.find_exact(**query).get()
    for track in tracks:
        for artist in track.artists:
            if artist.name:
                artists.add(('Artist', artist.name))
    return artists


def _list_album(context, query):
    albums = set()
    tracks = context.core.library.find_exact(**query).get()
    for track in tracks:
        if track.album and track.album.name:
            albums.add(('Album', track.album.name))
    return albums


def _list_date(context, query):
    dates = set()
    tracks = context.core.library.find_exact(**query).get()
    for track in tracks:
        if track.date:
            dates.add(('Date', track.date))
    return dates


@handle_request(r'^listall "(?P<uri>[^"]+)"')
def listall(context, uri):
    """
    *musicpd.org, music database section:*

        ``listall [URI]``

        Lists all songs and directories in ``URI``.
    """
    raise MpdNotImplemented  # TODO


@handle_request(r'^listallinfo "(?P<uri>[^"]+)"')
def listallinfo(context, uri):
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


@handle_request(
    r'^search (?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Dd]ate|[Ff]ile[name]*|'
    r'[Tt]itle|[Aa]ny)"? "[^"]*"\s?)+)$')
def search(context, mpd_query):
    """
    *musicpd.org, music database section:*

        ``search {TYPE} {WHAT}``

        Searches for any song that contains ``WHAT``. ``TYPE`` can be
        ``title``, ``artist``, ``album`` or ``filename``. Search is not
        case sensitive.

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
        query = _build_query(mpd_query)
    except ValueError:
        return
    return tracks_to_mpd_format(
        context.core.library.search(**query).get())


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
