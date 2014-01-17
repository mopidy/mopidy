from __future__ import unicode_literals

import re
import shlex

from mopidy.mpd.exceptions import MpdArgError
from mopidy.models import TlTrack

# TODO: special handling of local:// uri scheme
normalize_path_re = re.compile(r'[^/]+')


def normalize_path(path, relative=False):
    parts = normalize_path_re.findall(path or '')
    if not relative:
        parts.insert(0, '')
    return '/'.join(parts)


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
    ]

    if track.date:
        result.append(('Date', track.date))

    if track.album is not None and track.album.num_tracks != 0:
        result.append(('Track', '%d/%d' % (
            track.track_no, track.album.num_tracks)))
    else:
        result.append(('Track', track.track_no))
    if position is not None and tlid is not None:
        result.append(('Pos', position))
        result.append(('Id', tlid))
    if track.album is not None and track.album.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_ALBUMID', track.album.musicbrainz_id))
    # FIXME don't use first and best artist?
    # FIXME don't duplicate following code?
    if track.album is not None and track.album.artists:
        artists = artists_to_mpd_format(track.album.artists)
        result.append(('AlbumArtist', artists))
        artists = filter(
            lambda a: a.musicbrainz_id is not None, track.album.artists)
        if artists:
            result.append(
                ('MUSICBRAINZ_ALBUMARTISTID', artists[0].musicbrainz_id))
    if track.artists:
        artists = filter(lambda a: a.musicbrainz_id is not None, track.artists)
        if artists:
            result.append(('MUSICBRAINZ_ARTISTID', artists[0].musicbrainz_id))

    if track.composers:
        result.append(('Composer', artists_to_mpd_format(track.composers)))

    if track.performers:
        result.append(('Performer', artists_to_mpd_format(track.performers)))

    if track.genre:
        result.append(('Genre', track.genre))

    if track.disc_no:
        result.append(('Disc', track.disc_no))

    if track.comment:
        result.append(('Comment', track.comment))

    if track.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_TRACKID', track.musicbrainz_id))
    return result


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


def query_from_mpd_list_format(field, mpd_query):
    """
    Converts an MPD ``list`` query to a Mopidy query.
    """
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
            value = tokens[1]
            tokens = tokens[2:]
            if key not in ('artist', 'album', 'albumartist', 'composer',
                           'date', 'genre', 'performer'):
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
