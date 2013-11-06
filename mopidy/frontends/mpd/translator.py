from __future__ import unicode_literals

import os
import re
import shlex
import urllib

from mopidy.frontends.mpd import protocol
from mopidy.frontends.mpd.exceptions import MpdArgError
from mopidy.models import TlTrack
from mopidy.utils.path import mtime as get_mtime, uri_to_path, split_path

# TODO: special handling of local:// uri scheme


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
            if key not in ('artist', 'album', 'albumartist', 'date', 'genre'):
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


# XXX The regexps below should be refactored to reuse common patterns here
# and in mopidy.frontends.mpd.protocol.music_db.QUERY_RE.

MPD_SEARCH_QUERY_RE = re.compile(r"""
    \b                  # Only begin matching at word bundaries
    "?                  # Optional quote around the field type
    (?:                 # A non-capturing group for the field type
        [Aa]lbum
      | [Aa]rtist
      | [Aa]lbumartist
      | [Dd]ate
      | [Ff]ile
      | [Ff]ilename
      | [Tt]itle
      | [Tt]rack
      | [Aa]ny
    )
    "?                  # End of optional quote around the field type
    \s                  # A single space
    "[^"]+"             # Matching a quoted search string
""", re.VERBOSE)

MPD_SEARCH_QUERY_PART_RE = re.compile(r"""
    \b                  # Only begin matching at word bundaries
    "?                  # Optional quote around the field type
    (?P<field>(         # A capturing group for the field type
        [Aa]lbum
      | [Aa]rtist
      | [Aa]lbumartist
      | [Dd]ate
      | [Ff]ile
      | [Ff]ilename
      | [Tt]itle
      | [Tt]rack
      | [Aa]ny
    ))
    "?                  # End of optional quote around the field type
    \s                  # A single space
    "(?P<what>[^"]+)"   # Capturing a quoted search string
""", re.VERBOSE)


def query_from_mpd_search_format(mpd_query):
    """
    Parses an MPD ``search`` or ``find`` query and converts it to the Mopidy
    query format.

    :param mpd_query: the MPD search query
    :type mpd_query: string
    """
    query_parts = MPD_SEARCH_QUERY_RE.findall(mpd_query)
    query = {}
    for query_part in query_parts:
        m = MPD_SEARCH_QUERY_PART_RE.match(query_part)
        field = m.groupdict()['field'].lower()
        if field == 'title':
            field = 'track_name'
        elif field == 'track':
            field = 'track_no'
        elif field in ('file', 'filename'):
            field = 'uri'
        what = m.groupdict()['what']
        if not what:
            raise ValueError
        if field in query:
            query[field].append(what)
        else:
            query[field] = [what]
    return query


# TODO: move to tagcache backend.
def tracks_to_tag_cache_format(tracks, media_dir):
    """
    Format list of tracks for output to MPD tag cache

    :param tracks: the tracks
    :type tracks: list of :class:`mopidy.models.Track`
    :param media_dir: the path to the music dir
    :type media_dir: string
    :rtype: list of lists of two-tuples
    """
    result = [
        ('info_begin',),
        ('mpd_version', protocol.VERSION),
        ('fs_charset', protocol.ENCODING),
        ('info_end',)
    ]
    tracks.sort(key=lambda t: t.uri)
    dirs, files = tracks_to_directory_tree(tracks, media_dir)
    _add_to_tag_cache(result, dirs, files, media_dir)
    return result


# TODO: bytes only
def _add_to_tag_cache(result, dirs, files, media_dir):
    base_path = media_dir.encode('utf-8')

    for path, (entry_dirs, entry_files) in dirs.items():
        try:
            text_path = path.decode('utf-8')
        except UnicodeDecodeError:
            text_path = urllib.quote(path).decode('utf-8')
        name = os.path.split(text_path)[1]
        result.append(('directory', text_path))
        result.append(('mtime', get_mtime(os.path.join(base_path, path))))
        result.append(('begin', name))
        _add_to_tag_cache(result, entry_dirs, entry_files, media_dir)
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

        # TODO: use track.last_modified
        track_result['file'] = relative_uri
        track_result['mtime'] = get_mtime(path)
        track_result['key'] = os.path.basename(text_path)
        track_result = order_mpd_track_info(track_result.items())

        result.extend(track_result)

    result.append(('songList end',))


def tracks_to_directory_tree(tracks, media_dir):
    directories = ({}, [])

    for track in tracks:
        path = b''
        current = directories

        absolute_track_dir_path = os.path.dirname(uri_to_path(track.uri))
        relative_track_dir_path = re.sub(
            '^' + re.escape(media_dir), b'', absolute_track_dir_path)

        for part in split_path(relative_track_dir_path):
            path = os.path.join(path, part)
            if path not in current[0]:
                current[0][path] = ({}, [])
            current = current[0][path]
        current[1].append(track)
    return directories
