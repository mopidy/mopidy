from __future__ import unicode_literals

import os
import re
import urllib

from mopidy import settings
from mopidy.frontends.mpd import protocol
from mopidy.models import TlTrack
from mopidy.utils.path import mtime as get_mtime, uri_to_path, split_path


def track_to_mpd_format(track, position=None):
    """
    Format track for output to MPD client.

    :param track: the track
    :type track: :class:`mopidy.models.Track` or :class:`mopidy.models.TlTrack`
    :param position: track's position in playlist
    :type position: integer
    :param key: if we should set key
    :type key: boolean
    :param mtime: if we should set mtime
    :type mtime: boolean
    :rtype: list of two-tuples
    """
    if isinstance(track, TlTrack):
        (tlid, track) = track
    else:
        (tlid, track) = (None, track)
    result = [
        ('file', track.uri or ''),
        ('Time', track.length and (track.length // 1000) or 0),
        ('Artist', artists_to_mpd_format(track.artists)),
        ('Title', track.name or ''),
        ('Album', track.album and track.album.name or ''),
        ('Date', track.date or ''),
    ]
    if track.album is not None and track.album.num_tracks != 0:
        result.append(('Track', '%d/%d' % (
            track.track_no, track.album.num_tracks)))
    else:
        result.append(('Track', track.track_no))
    if track.album is not None and track.album.artists:
        artists = artists_to_mpd_format(track.album.artists)
        result.append(('AlbumArtist', artists))
    if position is not None and tlid is not None:
        result.append(('Pos', position))
        result.append(('Id', tlid))
    if track.album is not None and track.album.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_ALBUMID', track.album.musicbrainz_id))
    # FIXME don't use first and best artist?
    # FIXME don't duplicate following code?
    if track.album is not None and track.album.artists:
        artists = filter(
            lambda a: a.musicbrainz_id is not None, track.album.artists)
        if artists:
            result.append(
                ('MUSICBRAINZ_ALBUMARTISTID', artists[0].musicbrainz_id))
    if track.artists:
        artists = filter(lambda a: a.musicbrainz_id is not None, track.artists)
        if artists:
            result.append(('MUSICBRAINZ_ARTISTID', artists[0].musicbrainz_id))
    if track.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_TRACKID', track.musicbrainz_id))
    return result


MPD_KEY_ORDER = '''
    key file Time Artist AlbumArtist Title Album Track Date MUSICBRAINZ_ALBUMID
    MUSICBRAINZ_ALBUMARTISTID MUSICBRAINZ_ARTISTID MUSICBRAINZ_TRACKID mtime
'''.split()


def order_mpd_track_info(result):
    """
    Order results from
    :func:`mopidy.frontends.mpd.translator.track_to_mpd_format` so that it
    matches MPD's ordering. Simply a cosmetic fix for easier diffing of
    tag_caches.

    :param result: the track info
    :type result: list of tuples
    :rtype: list of tuples
    """
    return sorted(result, key=lambda i: MPD_KEY_ORDER.index(i[0]))


def artists_to_mpd_format(artists):
    """
    Format track artists for output to MPD client.

    :param artists: the artists
    :type track: array of :class:`mopidy.models.Artist`
    :rtype: string
    """
    artists = list(artists)
    artists.sort(key=lambda a: a.name)
    return ', '.join([a.name for a in artists if a.name])


def tracks_to_mpd_format(tracks, start=0, end=None):
    """
    Format list of tracks for output to MPD client.

    Optionally limit output to the slice ``[start:end]`` of the list.

    :param tracks: the tracks
    :type tracks: list of :class:`mopidy.models.Track` or
        :class:`mopidy.models.TlTrack`
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
    assert len(tracks) == len(positions)
    result = []
    for track, position in zip(tracks, positions):
        result.append(track_to_mpd_format(track, position))
    return result


def playlist_to_mpd_format(playlist, *args, **kwargs):
    """
    Format playlist for output to MPD client.

    Arguments as for :func:`tracks_to_mpd_format`, except the first one.
    """
    return tracks_to_mpd_format(playlist.tracks, *args, **kwargs)


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
    tracks.sort(key=lambda t: t.uri)
    _add_to_tag_cache(result, *tracks_to_directory_tree(tracks))
    return result


def _add_to_tag_cache(result, folders, files):
    base_path = settings.LOCAL_MUSIC_PATH.encode('utf-8')

    for path, entry in folders.items():
        try:
            text_path = path.decode('utf-8')
        except UnicodeDecodeError:
            text_path = urllib.quote(path).decode('utf-8')
        name = os.path.split(text_path)[1]
        result.append(('directory', text_path))
        result.append(('mtime', get_mtime(os.path.join(base_path, path))))
        result.append(('begin', name))
        _add_to_tag_cache(result, *entry)
        result.append(('end', name))

    result.append(('songList begin',))

    for track in files:
        track_result = dict(track_to_mpd_format(track))

        path = uri_to_path(track_result['file'])
        try:
            text_path = path.decode('utf-8')
        except UnicodeDecodeError:
            text_path = urllib.quote(path).decode('utf-8')
        relative_path = os.path.relpath(path, base_path)
        relative_uri = urllib.quote(relative_path)

        track_result['file'] = relative_uri
        track_result['mtime'] = get_mtime(path)
        track_result['key'] = os.path.basename(text_path)
        track_result = order_mpd_track_info(track_result.items())

        result.extend(track_result)

    result.append(('songList end',))


def tracks_to_directory_tree(tracks):
    directories = ({}, [])

    for track in tracks:
        path = b''
        current = directories

        absolute_track_dir_path = os.path.dirname(uri_to_path(track.uri))
        relative_track_dir_path = re.sub(
            '^' + re.escape(settings.LOCAL_MUSIC_PATH), b'',
            absolute_track_dir_path)

        for part in split_path(relative_track_dir_path):
            path = os.path.join(path, part)
            if path not in current[0]:
                current[0][path] = ({}, [])
            current = current[0][path]
        current[1].append(track)
    return directories
