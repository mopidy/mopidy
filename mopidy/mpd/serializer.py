def track_to_mpd_format(track, position=0, search_result=False):
    """
    Format track for output to MPD client.

    :param track: the track
    :type track: :class:`mopidy.models.Track`
    :param position: track's position in playlist
    :type position: integer
    :param search_result: format for output in search result
    :type search_result: boolean
    :rtype: list of two-tuples
    """
    result = [
        ('file', track.uri or ''),
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
    if not search_result:
        result.append(('Pos', position))
        result.append(('Id', track.id or position))
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

def playlist_to_mpd_format(playlist, start=0, end=None, search_result=False):
    """
    Format playlist for output to MPD client.

    Optionally limit output to the slice ``[start:end]`` of the playlist.

    :param playlist: the playlist
    :type playlist: :class:`mopidy.models.Playlist`
    :param start: position of first track to include in output
    :type start: int (positive or negative)
    :param end: position after last track to include in output
    :type end: int (positive or negative) or :class:`None` for end of list
    :rtype: list of lists of two-tuples
    """
    if start < 0:
        range_start = playlist.length + start
    else:
        range_start = start
    if end is not None and end < 0:
        range_end = playlist.length - end
    elif end is not None and end >= 0:
        range_end = end
    else:
        range_end = playlist.length
    tracks = []
    for track, position in zip(playlist.tracks[start:end],
            range(range_start, range_end)):
        tracks.append(track.mpd_format(position, search_result))
    return tracks
