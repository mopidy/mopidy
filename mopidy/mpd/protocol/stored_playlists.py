from __future__ import absolute_import, division, unicode_literals

import datetime
import warnings

from mopidy.mpd import exceptions, protocol, translator


@protocol.commands.add('listplaylist')
def listplaylist(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``listplaylist {NAME}``

        Lists the files in the playlist ``NAME.m3u``.

    Output format::

        file: relative/path/to/file1.flac
        file: relative/path/to/file2.ogg
        file: relative/path/to/file3.mp3
    """
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        raise exceptions.MpdNoExistError('No such playlist')
    return ['file: %s' % t.uri for t in playlist.tracks]


@protocol.commands.add('listplaylistinfo')
def listplaylistinfo(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``listplaylistinfo {NAME}``

        Lists songs in the playlist ``NAME.m3u``.

    Output format:

        Standard track listing, with fields: file, Time, Title, Date,
        Album, Artist, Track
    """
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        raise exceptions.MpdNoExistError('No such playlist')
    return translator.playlist_to_mpd_format(playlist)


@protocol.commands.add('listplaylists')
def listplaylists(context):
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

    *Clarifications:*

    - ncmpcpp 0.5.10 segfaults if we return 'playlist: ' on a line, so we must
      ignore playlists without names, which isn't very useful anyway.
    """
    last_modified = _get_last_modified()
    result = []
    for playlist_ref in context.core.playlists.as_list().get():
        if not playlist_ref.name:
            continue
        name = context.lookup_playlist_name_from_uri(playlist_ref.uri)
        result.append(('playlist', name))
        result.append(('Last-Modified', last_modified))
    return result


# TODO: move to translators?
def _get_last_modified(last_modified=None):
    """Formats last modified timestamp of a playlist for MPD.

    Time in UTC with second precision, formatted in the ISO 8601 format, with
    the "Z" time zone marker for UTC. For example, "1970-01-01T00:00:00Z".
    """
    if last_modified is None:
        # If unknown, assume the playlist is modified
        dt = datetime.datetime.utcnow()
    else:
        dt = datetime.datetime.utcfromtimestamp(last_modified / 1000.0)
    dt = dt.replace(microsecond=0)
    return '%sZ' % dt.isoformat()


@protocol.commands.add('load', playlist_slice=protocol.RANGE)
def load(context, name, playlist_slice=slice(0, None)):
    """
    *musicpd.org, stored playlists section:*

        ``load {NAME} [START:END]``

        Loads the playlist into the current queue. Playlist plugins are
        supported. A range may be specified to load only a part of the
        playlist.

    *Clarifications:*

    - ``load`` appends the given playlist to the current playlist.

    - MPD 0.17.1 does not support open-ended ranges, i.e. without end
      specified, for the ``load`` command, even though MPD's general range docs
      allows open-ended ranges.

    - MPD 0.17.1 does not fail if the specified range is outside the playlist,
      in either or both ends.
    """
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        raise exceptions.MpdNoExistError('No such playlist')

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', 'tracklist.add.*"tracks".*')
        context.core.tracklist.add(playlist.tracks[playlist_slice]).get()


@protocol.commands.add('playlistadd')
def playlistadd(context, name, uri):
    """
    *musicpd.org, stored playlists section:*

        ``playlistadd {NAME} {URI}``

        Adds ``URI`` to the playlist ``NAME.m3u``.

        ``NAME.m3u`` will be created if it does not exist.
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('playlistclear')
def playlistclear(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``playlistclear {NAME}``

        Clears the playlist ``NAME.m3u``.
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('playlistdelete', songpos=protocol.UINT)
def playlistdelete(context, name, songpos):
    """
    *musicpd.org, stored playlists section:*

        ``playlistdelete {NAME} {SONGPOS}``

        Deletes ``SONGPOS`` from the playlist ``NAME.m3u``.
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add(
    'playlistmove', from_pos=protocol.UINT, to_pos=protocol.UINT)
def playlistmove(context, name, from_pos, to_pos):
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
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('rename')
def rename(context, old_name, new_name):
    """
    *musicpd.org, stored playlists section:*

        ``rename {NAME} {NEW_NAME}``

        Renames the playlist ``NAME.m3u`` to ``NEW_NAME.m3u``.
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('rm')
def rm(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``rm {NAME}``

        Removes the playlist ``NAME.m3u`` from the playlist directory.
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('save')
def save(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``save {NAME}``

        Saves the current playlist to ``NAME.m3u`` in the playlist
        directory.
    """
    raise exceptions.MpdNotImplemented  # TODO
