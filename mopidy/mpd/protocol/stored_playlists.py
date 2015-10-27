from __future__ import absolute_import, division, unicode_literals

import datetime
import logging
import urlparse
import warnings

from mopidy.mpd import exceptions, protocol, translator

logger = logging.getLogger(__name__)


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
def playlistadd(context, name, track_uri):
    """
    *musicpd.org, stored playlists section:*

        ``playlistadd {NAME} {URI}``

        Adds ``URI`` to the playlist ``NAME.m3u``.

        ``NAME.m3u`` will be created if it does not exist.
    """
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        # Create new playlist with this single track
        lookup_res = context.core.library.lookup(uris=[track_uri]).get()
        tracks = [track for selections in lookup_res.values() for track in selections]
        _create_playlist(context, name, tracks)
    else:
        # Add track to existing playlist
        uri_scheme = urlparse.urlparse(track_uri).scheme
        lookup_res = context.core.library.lookup(uris=[track_uri]).get()
        to_add = [track for selections in lookup_res.values() for track in selections]
        playlist = playlist.replace(tracks=list(playlist.tracks) + to_add)
        if context.core.playlists.save(playlist).get() is None:
            playlist_scheme = urlparse.urlparse(playlist.uri).scheme
            raise exceptions.MpdInvalidTrackForPlaylist(
                playlist_scheme, uri_scheme)


def _create_playlist(context, name, tracks):
    """
    Creates new playlist using backend appropriate for the given tracks
    """
    uri_schemes = set([urlparse.urlparse(t.uri).scheme for t in tracks])
    for scheme in uri_schemes:
        playlist = context.core.playlists.create(name, scheme).get()
        if not playlist:
            # Backend can't create playlists at all
            logger.warning("%s backend can't create playlists", scheme)
            continue
        playlist = playlist.replace(tracks=tracks)
        if context.core.playlists.save(playlist).get() is None:
            # Failed to save using this backend
            continue
        # Created and saved
        return
    # Can't use backend appropriate for passed uri schemes, use default one
    default_scheme = context.dispatcher.config['mpd']['default_playlist_scheme']
    playlist = context.core.playlists.create(name, default_scheme).get()
    if not playlist:
        # If even MPD's default backend can't save playlist, everything is lost
        logger.warning("Default backend can't create playlists")
        raise exceptions.MpdFailedToSavePlaylist(None)
    playlist = playlist.replace(tracks=tracks)
    if context.core.playlists.save(playlist).get() is None:
        uri_scheme = urlparse.urlparse(playlist.uri).scheme
        raise exceptions.MpdFailedToSavePlaylist(uri_scheme)


@protocol.commands.add('playlistclear')
def playlistclear(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``playlistclear {NAME}``

        Clears the playlist ``NAME.m3u``.

    ``NAME.m3u`` will be created if it does not exist.
    """
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        playlist = context.core.playlists.create(name).get()

    # Just replace tracks with empty list and save
    playlist = playlist.replace(tracks=[])
    if context.core.playlists.save(playlist).get() is None:
        raise exceptions.MpdFailedToSavePlaylist(urlparse.urlparse(uri).scheme)


@protocol.commands.add('playlistdelete', songpos=protocol.UINT)
def playlistdelete(context, name, songpos):
    """
    *musicpd.org, stored playlists section:*

        ``playlistdelete {NAME} {SONGPOS}``

        Deletes ``SONGPOS`` from the playlist ``NAME.m3u``.
    """
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        raise exceptions.MpdNoExistError('No such playlist')

    # Convert tracks to list and remove requested
    tracks = list(playlist.tracks)
    tracks.pop(songpos)

    # Replace tracks and save playlist
    playlist = playlist.replace(tracks=tracks)
    if context.core.playlists.save(playlist).get() is None:
        raise exceptions.MpdFailedToSavePlaylist(urlparse.urlparse(uri).scheme)


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
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        raise exceptions.MpdNoExistError('No such playlist')
    if from_pos == to_pos:
        return  # Nothing to do

    # Convert tracks to list and perform move
    tracks = list(playlist.tracks)
    track = tracks.pop(from_pos)
    tracks.insert(to_pos, track)

    # Replace tracks and save playlist
    playlist = playlist.replace(tracks=tracks)
    if context.core.playlists.save(playlist).get() is None:
        raise exceptions.MpdFailedToSavePlaylist(urlparse.urlparse(uri).scheme)


@protocol.commands.add('rename')
def rename(context, old_name, new_name):
    """
    *musicpd.org, stored playlists section:*

        ``rename {NAME} {NEW_NAME}``

        Renames the playlist ``NAME.m3u`` to ``NEW_NAME.m3u``.
    """
    uri = context.lookup_playlist_uri_from_name(old_name)
    uri_scheme = urlparse.urlparse(uri).scheme
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        raise exceptions.MpdNoExistError('No such playlist')

    # Create copy of the playlist and remove original
    copy = context.core.playlists.create(new_name, uri_scheme).get()
    copy = copy.replace(tracks=playlist.tracks)
    context.core.playlists.save(copy).get()
    context.core.playlists.delete(uri).get()


@protocol.commands.add('rm')
def rm(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``rm {NAME}``

        Removes the playlist ``NAME.m3u`` from the playlist directory.
    """
    uri = context.lookup_playlist_uri_from_name(name)
    context.core.playlists.delete(uri).get()


@protocol.commands.add('save')
def save(context, name):
    """
    *musicpd.org, stored playlists section:*

        ``save {NAME}``

        Saves the current playlist to ``NAME.m3u`` in the playlist
        directory.
    """
    tracks = context.core.tracklist.get_tracks().get()
    uri = context.lookup_playlist_uri_from_name(name)
    playlist = uri is not None and context.core.playlists.lookup(uri).get()
    if not playlist:
        # Create new playlist
        _create_playlist(context, name, tracks)
    else:
        # Overwrite existing playlist
        playlist = playlist.replace(tracks=tracks)
        if not context.core.playlists.save(playlist).get():
            raise exceptions.MpdFailedToSavePlaylist(
                urlparse.urlparse(uri).scheme)
