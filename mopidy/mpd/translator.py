from __future__ import absolute_import, unicode_literals

import re

from mopidy.models import TlTrack

# TODO: special handling of local:// uri scheme
normalize_path_re = re.compile(r'[^/]+')


def normalize_path(path, relative=False):
    parts = normalize_path_re.findall(path or '')
    if not relative:
        parts.insert(0, '')
    return '/'.join(parts)


def track_to_mpd_format(track, position=None, stream_title=None):
    """
    Format track for output to MPD client.

    :param track: the track
    :type track: :class:`mopidy.models.Track` or :class:`mopidy.models.TlTrack`
    :param position: track's position in playlist
    :type position: integer
    :param stream_title: the current streams title
    :type position: string
    :rtype: list of two-tuples
    """
    if isinstance(track, TlTrack):
        (tlid, track) = track
    else:
        (tlid, track) = (None, track)

    result = [
        ('file', track.uri or ''),
        # TODO: only show length if not none, see:
        # https://github.com/mopidy/mopidy/issues/923#issuecomment-79584110
        ('Time', track.length and (track.length // 1000) or 0),
        ('Artist', concatenate_multiple_values(track.artists, 'name')),
        ('Title', track.name or ''),
        ('Album', track.album and track.album.name or ''),
    ]

    if stream_title:
        result.append(('Name', stream_title))

    if track.date:
        result.append(('Date', track.date))

    if track.album is not None and track.album.num_tracks is not None:
        result.append(('Track', '%d/%d' % (
            track.track_no or 0, track.album.num_tracks)))
    else:
        result.append(('Track', track.track_no or 0))
    if position is not None and tlid is not None:
        result.append(('Pos', position))
        result.append(('Id', tlid))
    if track.album is not None and track.album.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_ALBUMID', track.album.musicbrainz_id))

    if track.album is not None and track.album.artists:
        result.append(
            ('AlbumArtist',
                concatenate_multiple_values(track.album.artists, 'name')))
        musicbrainz_ids = concatenate_multiple_values(
            track.album.artists, 'musicbrainz_id')
        if musicbrainz_ids:
            result.append(('MUSICBRAINZ_ALBUMARTISTID', musicbrainz_ids))

    if track.artists:
        musicbrainz_ids = concatenate_multiple_values(
            track.artists, 'musicbrainz_id')
        if musicbrainz_ids:
            result.append(('MUSICBRAINZ_ARTISTID', musicbrainz_ids))

    if track.composers:
        result.append(
            (
                'Composer',
                concatenate_multiple_values(track.composers, 'name')
            )
        )

    if track.performers:
        result.append(
            (
                'Performer',
                concatenate_multiple_values(track.performers, 'name')
            )
        )

    if track.genre:
        result.append(('Genre', track.genre))

    if track.disc_no:
        result.append(('Disc', track.disc_no))

    if track.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_TRACKID', track.musicbrainz_id))
    return result


def concatenate_multiple_values(artists, attribute):
    """
    Format track artist values for output to MPD client.

    :param artists: the artists
    :type track: array of :class:`mopidy.models.Artist`
    :param attribute: the artist attribute to use
    :type string
    :rtype: string
    """
    # Don't sort the values. MPD doesn't appear to (or if it does it's not
    # strict alphabetical). If we just use them in the order in which they come
    # in then the musicbrainz ids have a higher chance of staying in sync
    return ';'.join(
        getattr(a, attribute)
        for a in artists if getattr(a, attribute, None) is not None
    )


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
