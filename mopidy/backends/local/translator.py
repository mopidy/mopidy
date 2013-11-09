from __future__ import unicode_literals

import logging
import os
import urlparse

from mopidy.models import Track, Artist, Album
from mopidy.utils.encoding import locale_decode
from mopidy.utils.path import path_to_uri, uri_to_path

logger = logging.getLogger('mopidy.backends.local')


def local_to_file_uri(uri, media_dir):
    # TODO: check that type is correct.
    file_path = uri_to_path(uri).split(b':', 1)[1]
    file_path = os.path.join(media_dir, file_path)
    return path_to_uri(file_path)


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

        if urlparse.urlsplit(line).scheme:
            uris.append(line)
        elif os.path.normpath(line) == os.path.abspath(line):
            path = path_to_uri(line)
            uris.append(path)
        else:
            path = path_to_uri(os.path.join(media_dir, line))
            uris.append(path)

    return uris


# TODO: remove music_dir from API
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
            _convert_mpd_data(current, tracks)
            current.clear()

        current[key.lower()] = value.decode('utf-8')

    _convert_mpd_data(current, tracks)

    return tracks


def _convert_mpd_data(data, tracks):
    if not data:
        return

    track_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    albumartist_kwargs = {}

    if 'track' in data:
        if '/' in data['track']:
            album_kwargs['num_tracks'] = int(data['track'].split('/')[1])
            track_kwargs['track_no'] = int(data['track'].split('/')[0])
        else:
            track_kwargs['track_no'] = int(data['track'])

    if 'mtime' in data:
        track_kwargs['last_modified'] = int(data['mtime'])

    if 'artist' in data:
        artist_kwargs['name'] = data['artist']

    if 'albumartist' in data:
        albumartist_kwargs['name'] = data['albumartist']

    if 'composer' in data:
        track_kwargs['composers'] = [Artist(name=data['composer'])]

    if 'performer' in data:
        track_kwargs['performers'] = [Artist(name=data['performer'])]

    if 'album' in data:
        album_kwargs['name'] = data['album']

    if 'title' in data:
        track_kwargs['name'] = data['title']

    if 'genre' in data:
        track_kwargs['genre'] = data['genre']

    if 'date' in data:
        track_kwargs['date'] = data['date']

    if 'comment' in data:
        track_kwargs['comment'] = data['comment']

    if 'musicbrainz_trackid' in data:
        track_kwargs['musicbrainz_id'] = data['musicbrainz_trackid']

    if 'musicbrainz_albumid' in data:
        album_kwargs['musicbrainz_id'] = data['musicbrainz_albumid']

    if 'musicbrainz_artistid' in data:
        artist_kwargs['musicbrainz_id'] = data['musicbrainz_artistid']

    if 'musicbrainz_albumartistid' in data:
        albumartist_kwargs['musicbrainz_id'] = (
            data['musicbrainz_albumartistid'])

    if artist_kwargs:
        artist = Artist(**artist_kwargs)
        track_kwargs['artists'] = [artist]

    if albumartist_kwargs:
        albumartist = Artist(**albumartist_kwargs)
        album_kwargs['artists'] = [albumartist]

    if album_kwargs:
        album = Album(**album_kwargs)
        track_kwargs['album'] = album

    if data['file'][0] == '/':
        path = data['file'][1:]
    else:
        path = data['file']

    track_kwargs['uri'] = 'local:track:%s' % path
    track_kwargs['length'] = int(data.get('time', 0)) * 1000

    track = Track(**track_kwargs)
    tracks.add(track)
