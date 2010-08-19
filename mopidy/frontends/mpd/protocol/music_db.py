import re

from mopidy.frontends.mpd.protocol import handle_pattern, stored_playlists
from mopidy.frontends.mpd.exceptions import MpdNotImplemented

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

@handle_pattern(r'^count "(?P<tag>[^"]+)" "(?P<needle>[^"]*)"$')
def count(frontend, tag, needle):
    """
    *musicpd.org, music database section:*

        ``count {TAG} {NEEDLE}``

        Counts the number of songs and their total playtime in the db
        matching ``TAG`` exactly.
    """
    return [('songs', 0), ('playtime', 0)] # TODO

@handle_pattern(r'^find '
     r'(?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny)"?'
     ' "[^"]+"\s?)+)$')
def find(frontend, mpd_query):
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
    """
    query = _build_query(mpd_query)
    return frontend.backend.library.find_exact(**query).mpd_format()

@handle_pattern(r'^findadd '
     r'(?P<query>("?([Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny)"? '
     '"[^"]+"\s?)+)$')
def findadd(frontend, query):
    """
    *musicpd.org, music database section:*

        ``findadd {TYPE} {WHAT}``

        Finds songs in the db that are exactly ``WHAT`` and adds them to
        current playlist. ``TYPE`` can be any tag supported by MPD.
        ``WHAT`` is what to find.
    """
    # TODO Add result to current playlist
    #result = frontend.find(query)

@handle_pattern(r'^list (?P<field>[Aa]rtist)$')
@handle_pattern(r'^list "(?P<field>[Aa]rtist)"$')
@handle_pattern(r'^list (?P<field>album( artist)?)'
    '( "(?P<artist>[^"]+)")*$')
@handle_pattern(r'^list "(?P<field>album(" "artist)?)"'
    '( "(?P<artist>[^"]+)")*$')
def list_(frontend, field, artist=None):
    """
    *musicpd.org, music database section:*

        ``list {TYPE} [ARTIST]``

        Lists all tags of the specified type. ``TYPE`` should be ``album``,
        ``artist``, ``date``, or ``genre``.

        ``ARTIST`` is an optional parameter when type is ``album``,
        ``date``, or ``genre``.

        This filters the result list by an artist.

    *GMPC:*

    - does not add quotes around the field argument.
    - asks for "list artist" to get available artists and will not query
      for artist/album information if this is not retrived
    - asks for multiple fields, i.e.::

        list album artist "an artist name"

      returns the albums available for the asked artist::

        list album artist "Tiesto"
        Album: Radio Trance Vol 4-Promo-CD
        Album: Ur  A Tear in the Open CDR
        Album: Simple Trance 2004 Step One
        Album: In Concert 05-10-2003

    *ncmpc:*

    - does not add quotes around the field argument.
    - capitalizes the field argument.
    """
    field = field.lower()
    if field == u'artist':
        return _list_artist(frontend)
    elif field == u'album artist':
        return _list_album_artist(frontend, artist)
    # TODO More to implement

def _list_artist(frontend):
    """
    Since we don't know exactly all available artists, we respond with
    the artists we know for sure, which is all artists in our stored playlists.
    """
    artists = set()
    for playlist in frontend.backend.stored_playlists.playlists:
        for track in playlist.tracks:
            for artist in track.artists:
                artists.add((u'Artist', artist.name))
    return artists

def _list_album_artist(frontend, artist):
    playlist = frontend.backend.library.find_exact(artist=[artist])
    albums = set()
    for track in playlist.tracks:
        albums.add((u'Album', track.album.name))
    return albums

@handle_pattern(r'^listall "(?P<uri>[^"]+)"')
def listall(frontend, uri):
    """
    *musicpd.org, music database section:*

        ``listall [URI]``

        Lists all songs and directories in ``URI``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^listallinfo "(?P<uri>[^"]+)"')
def listallinfo(frontend, uri):
    """
    *musicpd.org, music database section:*

        ``listallinfo [URI]``

        Same as ``listall``, except it also returns metadata info in the
        same format as ``lsinfo``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^lsinfo$')
@handle_pattern(r'^lsinfo "(?P<uri>[^"]*)"$')
def lsinfo(frontend, uri=None):
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
        return stored_playlists.listplaylists(frontend)
    raise MpdNotImplemented # TODO

@handle_pattern(r'^rescan( "(?P<uri>[^"]+)")*$')
def rescan(frontend, uri=None):
    """
    *musicpd.org, music database section:*

        ``rescan [URI]``

        Same as ``update``, but also rescans unmodified files.
    """
    return update(frontend, uri, rescan_unmodified_files=True)

@handle_pattern(r'^search '
     r'(?P<mpd_query>("?([Aa]lbum|[Aa]rtist|[Ff]ilename|[Tt]itle|[Aa]ny)"?'
     ' "[^"]+"\s?)+)$')
def search(frontend, mpd_query):
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
    """
    query = _build_query(mpd_query)
    return frontend.backend.library.search(**query).mpd_format()

@handle_pattern(r'^update( "(?P<uri>[^"]+)")*$')
def update(frontend, uri=None, rescan_unmodified_files=False):
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
