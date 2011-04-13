import logging
import os

logger = logging.getLogger('mopidy.backends.local.translator')

from mopidy.models import Track, Artist, Album
from mopidy.utils.path import path_to_uri

def parse_m3u(file_path):
    """
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

    uris = []
    folder = os.path.dirname(file_path)

    try:
        with open(file_path) as m3u:
            contents = m3u.readlines()
    except IOError, e:
        logger.error('Couldn\'t open m3u: %s', e)
        return uris

    for line in contents:
        line = line.strip().decode('latin1')

        if line.startswith('#'):
            continue

        # FIXME what about other URI types?
        if line.startswith('file://'):
            uris.append(line)
        else:
            path = path_to_uri(folder, line)
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
    except IOError, e:
        logger.error('Could not open tag cache: %s', e)
        return tracks

    current = {}
    state = None

    for line in contents.split('\n'):
        if line == 'songList begin':
            state = 'songs'
            continue
        elif line == 'songList end':
            state = None
            continue
        elif not state:
            continue

        key, value = line.split(': ', 1)

        if key == 'key':
            _convert_mpd_data(current, tracks, music_dir)
            current.clear()

        current[key.lower()] = value.decode('utf-8')

    _convert_mpd_data(current, tracks, music_dir)

    return tracks

def _convert_mpd_data(data, tracks, music_dir):
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

    if 'artist' in data:
        artist_kwargs['name'] = data['artist']
        albumartist_kwargs['name'] = data['artist']

    if 'albumartist' in data:
        albumartist_kwargs['name'] = data['albumartist']

    if 'album' in data:
        album_kwargs['name'] = data['album']

    if 'title' in data:
        track_kwargs['name'] = data['title']

    if 'musicbrainz_trackid' in data:
        track_kwargs['musicbrainz_id'] = data['musicbrainz_trackid']

    if 'musicbrainz_albumid' in data:
        album_kwargs['musicbrainz_id'] = data['musicbrainz_albumid']

    if 'musicbrainz_artistid' in data:
        artist_kwargs['musicbrainz_id'] = data['musicbrainz_artistid']

    if 'musicbrainz_albumartistid' in data:
        albumartist_kwargs['musicbrainz_id'] = data['musicbrainz_albumartistid']

    if data['file'][0] == '/':
        path = data['file'][1:]
    else:
        path = data['file']

    if artist_kwargs:
        artist = Artist(**artist_kwargs)
        track_kwargs['artists'] = [artist]

    if albumartist_kwargs:
        albumartist = Artist(**albumartist_kwargs)
        album_kwargs['artists'] = [albumartist]
    
    if album_kwargs:
        album = Album(**album_kwargs)
        track_kwargs['album'] = album

    track_kwargs['uri'] = path_to_uri(music_dir, path)
    track_kwargs['length'] = int(data.get('time', 0)) * 1000

    track = Track(**track_kwargs)
    tracks.add(track)
