import datetime as dt

from mopidy.frontends.mpd.protocol import handle_pattern
from mopidy.frontends.mpd.exceptions import MpdNoExistError, MpdNotImplemented

@handle_pattern(r'^listplaylist "(?P<name>[^"]+)"$')
def listplaylist(frontend, name):
    """
    *musicpd.org, stored playlists section:*

        ``listplaylist {NAME}``

        Lists the files in the playlist ``NAME.m3u``.

    Output format::

        file: relative/path/to/file1.flac
        file: relative/path/to/file2.ogg
        file: relative/path/to/file3.mp3
    """
    try:
        playlist = frontend.backend.stored_playlists.get(name=name).get()
        return ['file: %s' % t.uri for t in playlist.tracks]
    except LookupError:
        raise MpdNoExistError(u'No such playlist', command=u'listplaylist')

@handle_pattern(r'^listplaylistinfo "(?P<name>[^"]+)"$')
def listplaylistinfo(frontend, name):
    """
    *musicpd.org, stored playlists section:*

        ``listplaylistinfo {NAME}``

        Lists songs in the playlist ``NAME.m3u``.

    Output format:

        Standard track listing, with fields: file, Time, Title, Date,
        Album, Artist, Track
    """
    try:
        playlist = frontend.backend.stored_playlists.get(name=name).get()
        return playlist.mpd_format()
    except LookupError:
        raise MpdNoExistError(
            u'No such playlist', command=u'listplaylistinfo')

@handle_pattern(r'^listplaylists$')
def listplaylists(frontend):
    """
    *musicpd.org, stored playlists section:*

        ``listplaylists``

        Prints a list of the playlist directory.

        After each playlist name the server sends its last modification
        time as attribute ``Last-Modified`` in ISO 8601 format. To avoid
        problems due to clock differences between clients and the server,
        clients should not compare this value with their local clock.

    Output format::

        playlist: a
        Last-Modified: 2010-02-06T02:10:25Z
        playlist: b
        Last-Modified: 2010-02-06T02:11:08Z
    """
    result = []
    for playlist in frontend.backend.stored_playlists.playlists.get():
        result.append((u'playlist', playlist.name))
        last_modified = (playlist.last_modified or
            dt.datetime.now()).isoformat()
        # Remove microseconds
        last_modified = last_modified.split('.')[0]
        # Add time zone information
        # TODO Convert to UTC before adding Z
        last_modified = last_modified + 'Z'
        result.append((u'Last-Modified', last_modified))
    return result

@handle_pattern(r'^load "(?P<name>[^"]+)"$')
def load(frontend, name):
    """
    *musicpd.org, stored playlists section:*

        ``load {NAME}``

        Loads the playlist ``NAME.m3u`` from the playlist directory.

    *Clarifications:*

    - ``load`` appends the given playlist to the current playlist.
    """
    try:
        playlist = frontend.backend.stored_playlists.get(name=name).get()
        frontend.backend.current_playlist.append(playlist.tracks)
    except LookupError:
        raise MpdNoExistError(u'No such playlist', command=u'load')

@handle_pattern(r'^playlistadd "(?P<name>[^"]+)" "(?P<uri>[^"]+)"$')
def playlistadd(frontend, name, uri):
    """
    *musicpd.org, stored playlists section:*

        ``playlistadd {NAME} {URI}``

        Adds ``URI`` to the playlist ``NAME.m3u``.

        ``NAME.m3u`` will be created if it does not exist.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^playlistclear "(?P<name>[^"]+)"$')
def playlistclear(frontend, name):
    """
    *musicpd.org, stored playlists section:*

        ``playlistclear {NAME}``

        Clears the playlist ``NAME.m3u``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^playlistdelete "(?P<name>[^"]+)" "(?P<songpos>\d+)"$')
def playlistdelete(frontend, name, songpos):
    """
    *musicpd.org, stored playlists section:*

        ``playlistdelete {NAME} {SONGPOS}``

        Deletes ``SONGPOS`` from the playlist ``NAME.m3u``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^playlistmove "(?P<name>[^"]+)" '
    r'"(?P<from_pos>\d+)" "(?P<to_pos>\d+)"$')
def playlistmove(frontend, name, from_pos, to_pos):
    """
    *musicpd.org, stored playlists section:*

        ``playlistmove {NAME} {SONGID} {SONGPOS}``

        Moves ``SONGID`` in the playlist ``NAME.m3u`` to the position
        ``SONGPOS``.

    *Clarifications:*

    - The second argument is not a ``SONGID`` as used elsewhere in the protocol
      documentation, but just the ``SONGPOS`` to move *from*, i.e.
      ``playlistmove {NAME} {FROM_SONGPOS} {TO_SONGPOS}``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^rename "(?P<old_name>[^"]+)" "(?P<new_name>[^"]+)"$')
def rename(frontend, old_name, new_name):
    """
    *musicpd.org, stored playlists section:*

        ``rename {NAME} {NEW_NAME}``

        Renames the playlist ``NAME.m3u`` to ``NEW_NAME.m3u``.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^rm "(?P<name>[^"]+)"$')
def rm(frontend, name):
    """
    *musicpd.org, stored playlists section:*

        ``rm {NAME}``

        Removes the playlist ``NAME.m3u`` from the playlist directory.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^save "(?P<name>[^"]+)"$')
def save(frontend, name):
    """
    *musicpd.org, stored playlists section:*

        ``save {NAME}``

        Saves the current playlist to ``NAME.m3u`` in the playlist
        directory.
    """
    raise MpdNotImplemented # TODO
