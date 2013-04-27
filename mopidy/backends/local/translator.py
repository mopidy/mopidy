from __future__ import unicode_literals

import logging
import urllib

from mopidy.models import Track, Artist, Album
from mopidy.utils.encoding import locale_decode
from mopidy.utils.path import path_to_uri

logger = logging.getLogger('mopidy.backends.local')


def parse_m3u(file_path, media_dir):
    r"""
    Convert M3U file list of uris

    Example M3U data::

        # This is a comment
        Alternative\Band - Song.mp3
        Classical\Other Band - New Song.mp3
        Stuff.mp3
        D:\More Music\Foo.mp3
        http://www.example.com:8000/Listen.pls
        http://www.example.com/~user/Mine.mp3

    - Relative paths of songs should be with respect to location of M3U.
    - Paths are normaly platform specific.
    - Lines starting with # should be ignored.
    - m3u files are latin-1.
    - This function does not bother with Extended M3U directives.
    """

    # TODO: uris as bytes
    uris = []
    try:
        with open(file_path) as m3u:
            contents = m3u.readlines()
    except IOError as error:
        logger.warning('Couldn\'t open m3u: %s', locale_decode(error))
        return uris

    for line in contents:
        line = line.strip().decode('latin1')

        if line.startswith('#'):
            continue

        # FIXME what about other URI types?
        if line.startswith('file://'):
            uris.append(line)
        else:
            path = path_to_uri(media_dir, line)
            uris.append(path)

    return uris


def parse_mpd_tag_cache(tag_cache, music_dir=''):
    """
    Converts a MPD tag_cache into a lists of tracks, artists and albums.
    """
    tracks = set()

    try:
        with open(tag_cache) as library:
            contents = library.read()
    except IOError as error:
        logger.warning('Could not open tag cache: %s', locale_decode(error))
        return tracks

    current = {}
    state = None

    # TODO: uris as bytes
    for line in contents.split(b'\n'):
        if line == b'songList begin':
            state = 'songs'
            continue
        elif line == b'songList end':
            state = None
            continue
        elif not state:
            continue

        key, value = line.split(b': ', 1)

        if key == b'key':
            _convert_mpd_data(current, tracks, music_dir)
            current.clear()

        current[key.lower()] = value.decode('utf-8')

    _convert_mpd_data(current, tracks, music_dir)

    return tracks


def _convert_mpd_data(data, tracks, music_dir):
    if not data:
        return

    # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
    # See https://github.com/mopidy/mopidy/issues/302 for details.

    track_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    albumartist_kwargs = {}

    if 'track' in data:
        if '/' in data['track']:
            album_kwargs[b'num_tracks'] = int(data['track'].split('/')[1])
            track_kwargs[b'track_no'] = int(data['track'].split('/')[0])
        else:
            track_kwargs[b'track_no'] = int(data['track'])

    if 'artist' in data:
        artist_kwargs[b'name'] = data['artist']
        albumartist_kwargs[b'name'] = data['artist']

    if 'albumartist' in data:
        albumartist_kwargs[b'name'] = data['albumartist']

    if 'album' in data:
        album_kwargs[b'name'] = data['album']

    if 'title' in data:
        track_kwargs[b'name'] = data['title']

    if 'date' in data:
        track_kwargs[b'date'] = data['date']

    if 'musicbrainz_trackid' in data:
        track_kwargs[b'musicbrainz_id'] = data['musicbrainz_trackid']

    if 'musicbrainz_albumid' in data:
        album_kwargs[b'musicbrainz_id'] = data['musicbrainz_albumid']

    if 'musicbrainz_artistid' in data:
        artist_kwargs[b'musicbrainz_id'] = data['musicbrainz_artistid']

    if 'musicbrainz_albumartistid' in data:
        albumartist_kwargs[b'musicbrainz_id'] = (
            data['musicbrainz_albumartistid'])

    if artist_kwargs:
        artist = Artist(**artist_kwargs)
        track_kwargs[b'artists'] = [artist]

    if albumartist_kwargs:
        albumartist = Artist(**albumartist_kwargs)
        album_kwargs[b'artists'] = [albumartist]

    if album_kwargs:
        album = Album(**album_kwargs)
        track_kwargs[b'album'] = album

    if data['file'][0] == '/':
        path = data['file'][1:]
    else:
        path = data['file']
    path = urllib.unquote(path.encode('utf-8'))

    if isinstance(music_dir, unicode):
        music_dir = music_dir.encode('utf-8')

    # Make sure we only pass bytestrings to path_to_uri to avoid implicit
    # decoding of bytestrings to unicode strings
    track_kwargs[b'uri'] = path_to_uri(music_dir, path)

    track_kwargs[b'length'] = int(data.get('time', 0)) * 1000

    track = Track(**track_kwargs)
    tracks.add(track)
