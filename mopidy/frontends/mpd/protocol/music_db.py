import re
import shlex

from mopidy.frontends.mpd.exceptions import MpdArgError, MpdNotImplemented
from mopidy.frontends.mpd.protocol import handle_request, stored_playlists
from mopidy.frontends.mpd.translator import playlist_to_mpd_format

def _build_query(mpd_query):
    """
    Parses a MPD query string and converts it to the Mopidy query format.
    """
    query_pattern = (
        r'"?(?:[Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny)"? "[^"]+"')
    query_parts = re.findall(query_pattern, mpd_query)
    query_part_pattern = (
        r'"?(?P<field>([Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny))"? '
        r'"(?P<what>[^"]+)"')
    query = {}
    for query_part in query_parts:
        m = re.match(query_part_pattern, query_part)
        field = m.groupdict()['field'].lower()
        if field == u'title':
            field = u'track'
        field = str(field) # Needed for kwargs keys on OS X and Windows
        what = m.groupdict()['what'].lower()
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
    return [('songs', 0), ('playtime', 0)] # TODO

@handle_request(r'^find '
     r'(?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Dd]ate|[Ff]ilename|'
     r'[Tt]itle|[Aa]ny)"? "[^"]+"\s?)+)$')
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
    """
    query = _build_query(mpd_query)
    return playlist_to_mpd_format(
        context.backend.library.find_exact(**query).get())

@handle_request(r'^findadd '
     r'(?P<query>("?([Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny)"? '
     '"[^"]+"\s?)+)$')
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

@handle_request(r'^list "?(?P<field>([Aa]rtist|[Aa]lbum|[Dd]ate|[Gg]enre))"?'
    '( (?P<mpd_query>.*))?$')
def list_(context, field, mpd_query=None):
    """
    *musicpd.org, music database section:*

        ``list {TYPE} [ARTIST]``

        Lists all tags of the specified type. ``TYPE`` should be ``album``,
        ``artist``, ``date``, or ``genre``.

        ``ARTIST`` is an optional parameter when type is ``album``,
        ``date``, or ``genre``.

        This filters the result list by an artist.

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
    query = _list_build_query(field, mpd_query)
    if field == u'artist':
        return _list_artist(context, query)
    elif field == u'album':
        return _list_album(context, query)
    elif field == u'date':
        return _list_date(context, query)
    elif field == u'genre':
        pass # TODO We don't have genre in our internal data structures yet

def _list_build_query(field, mpd_query):
    """Converts a ``list`` query to a Mopidy query."""
    if mpd_query is None:
        return {}
    try:
        # shlex does not seem to be friends with unicode objects
        tokens = shlex.split(mpd_query.encode('utf-8'))
    except ValueError as error:
        if error.message == 'No closing quotation':
            raise MpdArgError(u'Invalid unquoted character', command=u'list')
        else:
            raise error
    tokens = [t.decode('utf-8') for t in tokens]
    if len(tokens) == 1:
        if field == u'album':
            return {'artist': [tokens[0]]}
        else:
            raise MpdArgError(
                u'should be "Album" for 3 arguments', command=u'list')
    elif len(tokens) % 2 == 0:
        query = {}
        while tokens:
            key = tokens[0].lower()
            key = str(key) # Needed for kwargs keys on OS X and Windows
            value = tokens[1]
            tokens = tokens[2:]
            if key not in (u'artist', u'album', u'date', u'genre'):
                raise MpdArgError(u'not able to parse args', command=u'list')
            if key in query:
                query[key].append(value)
            else:
                query[key] = [value]
        return query
    else:
        raise MpdArgError(u'not able to parse args', command=u'list')

def _list_artist(context, query):
    artists = set()
    playlist = context.backend.library.find_exact(**query).get()
    for track in playlist.tracks:
        for artist in track.artists:
            artists.add((u'Artist', artist.name))
    return artists

def _list_album(context, query):
    albums = set()
    playlist = context.backend.library.find_exact(**query).get()
    for track in playlist.tracks:
        if track.album is not None:
            albums.add((u'Album', track.album.name))
    return albums

def _list_date(context, query):
    dates = set()
    playlist = context.backend.library.find_exact(**query).get()
    for track in playlist.tracks:
        if track.date is not None:
            dates.add((u'Date', track.date.strftime('%Y-%m-%d')))
    return dates

@handle_request(r'^listall "(?P<uri>[^"]+)"')
def listall(context, uri):
    """
    *musicpd.org, music database section:*

        ``listall [URI]``

        Lists all songs and directories in ``URI``.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^listallinfo "(?P<uri>[^"]+)"')
def listallinfo(context, uri):
    """
    *musicpd.org, music database section:*

        ``listallinfo [URI]``

        Same as ``listall``, except it also returns metadata info in the
        same format as ``lsinfo``.
    """
    raise MpdNotImplemented # TODO

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
    if uri is None or uri == u'/' or uri == u'':
        return stored_playlists.listplaylists(context)
    raise MpdNotImplemented # TODO

@handle_request(r'^rescan( "(?P<uri>[^"]+)")*$')
def rescan(context, uri=None):
    """
    *musicpd.org, music database section:*

        ``rescan [URI]``

        Same as ``update``, but also rescans unmodified files.
    """
    return update(context, uri, rescan_unmodified_files=True)

@handle_request(r'^search '
     r'(?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Dd]ate|[Ff]ilename|'
     r'[Tt]itle|[Aa]ny)"? "[^"]+"\s?)+)$')
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
    """
    query = _build_query(mpd_query)
    return playlist_to_mpd_format(
        context.backend.library.search(**query).get())

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
    return {'updating_db': 0} # TODO
