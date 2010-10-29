import os
import re

from mopidy import settings
from mopidy.frontends.mpd import protocol
from mopidy.utils.path import path_to_uri, uri_to_path, split_path

stat = os.stat

def track_to_mpd_format(track, position=None, cpid=None, key=False, mtime=False):
    """
    Format track for output to MPD client.

    :param track: the track
    :type track: :class:`mopidy.models.Track`
    :param position: track's position in playlist
    :type position: integer
    :param cpid: track's CPID (current playlist ID)
    :type cpid: integer
    :param key: if we should set key
    :type key: boolean
    :param mtime: if we should set mtime
    :type mtime: boolean
    :rtype: list of two-tuples
    """
    result = [
        ('file', uri_to_mpd_relative_path(track.uri) or ''),
        ('Time', track.length and (track.length // 1000) or 0),
        ('Artist', track_artists_to_mpd_format(track)),
        ('Title', track.name or ''),
        ('Album', track.album and track.album.name or ''),
        ('Date', track.date or ''),
    ]
    if track.album is not None and track.album.num_tracks != 0:
        result.append(('Track', '%d/%d' % (
            track.track_no, track.album.num_tracks)))
    else:
        result.append(('Track', track.track_no))
    if position is not None and cpid is not None:
        result.append(('Pos', position))
        result.append(('Id', cpid))
    if key and track.uri:
        result.insert(0, ('key', os.path.basename(uri_to_path(track.uri))))
    if mtime and track.uri:
        mtime = stat(uri_to_path(track.uri)).st_mtime
        result.append(('mtime', int(mtime)))
    return result

def track_artists_to_mpd_format(track):
    """
    Format track artists for output to MPD client.

    :param track: the track
    :type track: :class:`mopidy.models.Track`
    :rtype: string
    """
    artists = track.artists
    artists.sort(key=lambda a: a.name)
    return u', '.join([a.name for a in artists])

def tracks_to_mpd_format(tracks, start=0, end=None, cpids=None):
    """
    Format list of tracks for output to MPD client.

    Optionally limit output to the slice ``[start:end]`` of the list.

    :param tracks: the tracks
    :type tracks: list of :class:`mopidy.models.Track`
    :param start: position of first track to include in output
    :type start: int (positive or negative)
    :param end: position after last track to include in output
    :type end: int (positive or negative) or :class:`None` for end of list
    :rtype: list of lists of two-tuples
    """
    if end is None:
        end = len(tracks)
    tracks = tracks[start:end]
    positions = range(start, end)
    cpids = cpids and cpids[start:end] or [None for _ in tracks]
    assert len(tracks) == len(positions) == len(cpids)
    result = []
    for track, position, cpid in zip(tracks, positions, cpids):
        result.append(track_to_mpd_format(track, position, cpid))
    return result

def playlist_to_mpd_format(playlist, *args, **kwargs):
    """
    Format playlist for output to MPD client.

    Arguments as for :func:`tracks_to_mpd_format`, except the first one.
    """
    return tracks_to_mpd_format(playlist.tracks, *args, **kwargs)

def uri_to_mpd_relative_path(uri):
    """
    Strip uri and LOCAL_MUSIC_FOLDER part of uri.

    :param uri: the uri
    :type uri: string
    :rtype: string
    """
    if uri is None:
        return ''
    path = path_to_uri(settings.LOCAL_MUSIC_FOLDER)
    return re.sub('^' + re.escape(path), '', uri)

def tracks_to_tag_cache_format(tracks):
    """
    Format list of tracks for output to MPD tag cache

    :param tracks: the tracks
    :type tracks: list of :class:`mopidy.models.Track`
    :rtype: list of lists of two-tuples
    """
    result = [
        ('info_begin',),
        ('mpd_version', protocol.VERSION),
        ('fs_charset', protocol.ENCODING),
        ('info_end',)
    ]
    _add_to_tag_cache(result, *tracks_to_directory_tree(tracks))
    return result

def _add_to_tag_cache(result, folders, files):
    for path, entry in folders.items():
        name = os.path.split(path)[1]
        result.append(('directory', path))
        result.append(('mtime', stat(name).st_mtime))
        result.append(('begin', name))
        _add_to_tag_cache(result, *entry)
        result.append(('end', name))

    result.append(('songList begin',))
    for track in files:
        result.extend(track_to_mpd_format(track, key=True, mtime=True))
    result.append(('songList end',))

def tracks_to_directory_tree(tracks):
    directories = ({}, [])
    for track in tracks:
        uri = uri_to_mpd_relative_path(track.uri)
        path = ''
        current = directories
        for part in split_path(os.path.dirname(uri_to_path(uri))):
            path = os.path.join(path, part)
            print path
            if path not in current[0]:
                current[0][path] = ({}, [])
            current = current[0][path]
        current[1].append(track)
    return directories
