import logging
from multiprocessing.reduction import reduce_connection
import os
import pickle
import sys
import urllib

logger = logging.getLogger('mopidy.utils')

from mopidy.models import Track, Artist, Album

def flatten(the_list):
    result = []
    for element in the_list:
        if isinstance(element, list):
            result.extend(flatten(element))
        else:
            result.append(element)
    return result

def get_class(name):
    module_name = name[:name.rindex('.')]
    class_name = name[name.rindex('.') + 1:]
    logger.debug('Loading: %s', name)
    module = __import__(module_name, globals(), locals(), [class_name], -1)
    class_object = getattr(module, class_name)
    return class_object

def get_or_create_folder(folder):
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        logger.info(u'Creating %s', folder)
        os.mkdir(folder, 0755)
    return folder

def path_to_uri(*paths):
    path = os.path.join(*paths)
    path = path.encode('utf-8')
    if sys.platform == 'win32':
        return 'file:' + urllib.pathname2url(path)
    return 'file://' + urllib.pathname2url(path)

def indent(string, places=4, linebreak='\n'):
    lines = string.split(linebreak)
    if len(lines) == 1:
        return string
    result = u''
    for line in lines:
        result += linebreak + ' ' * places + line
    return result

def pickle_connection(connection):
    return pickle.dumps(reduce_connection(connection))

def unpickle_connection(pickled_connection):
    # From http://stackoverflow.com/questions/1446004
    (func, args) = pickle.loads(pickled_connection)
    return func(*args)

def spotify_uri_to_int(uri, output_bits=31):
    """
    Stable one-way translation from Spotify URI to 31-bit integer.

    Spotify track URIs has 62^22 possible values, which requires 131 bits of
    storage. The original MPD server uses 32-bit unsigned integers for track
    IDs. GMPC seems to think the track ID is a signed integer, thus we use 31
    output bits.

    In other words, this function throws away 100 bits of information. Since we
    only use the track IDs to identify a track within a single Mopidy instance,
    this information loss is acceptable. The chances of getting two different
    tracks with the same track ID loaded in the same Mopidy instance is still
    rather slim. 1 to 2,147,483,648 to be exact.

    Normal usage, with data loss::

        >>> spotify_uri_to_int('spotify:track:5KRRcT67VNIZUygEbMoIC1')
        624351954

    No data loss, may be converted back into a Spotify URI::

        >>> spotify_uri_to_int('spotify:track:5KRRcT67VNIZUygEbMoIC1',
        ...     output_bits=131)
        101411513484007705241035418492696638725L

    :param uri: Spotify URI on the format ``spotify:track:*``
    :type uri: string
    :param output_bits: number of bits of information kept in the return value
    :type output_bits: int
    :rtype: int
    """

    CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    BITS_PER_CHAR = 6 # int(math.ceil(math.log(len(CHARS), 2)))

    key = uri.split(':')[-1]
    full_id = 0
    for i, char in enumerate(key):
        full_id ^= CHARS.index(char) << BITS_PER_CHAR * i
    compressed_id = 0
    while full_id != 0:
        compressed_id ^= (full_id & (2 ** output_bits - 1))
        full_id >>= output_bits
    return int(compressed_id)

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

        current[key.lower()] = value

    _convert_mpd_data(current, tracks, music_dir)

    return tracks

def _convert_mpd_data(data, tracks, music_dir):
    if not data:
        return

    track_kwargs = {}
    album_kwargs = {}

    if 'track' in data:
        album_kwargs['num_tracks'] = int(data['track'].split('/')[1])
        track_kwargs['track_no'] = int(data['track'].split('/')[0])

    if 'artist' in data:
        artist = Artist(name=data['artist'])
        track_kwargs['artists'] = [artist]
        album_kwargs['artists'] = [artist]

    if 'album' in data:
        album_kwargs['name'] = data['album']
        album = Album(**album_kwargs)
        track_kwargs['album'] = album

    if 'title' in data:
        track_kwargs['name'] = data['title']

    if data['file'][0] == '/':
        path = os.path.join(music_dir, data['file'][1:])
    else:
        path = os.path.join(music_dir, data['file'])

    track_kwargs['uri'] = path_to_uri(path)
    track_kwargs['length'] = int(data.get('time', 0)) * 1000

    track = Track(**track_kwargs)
    tracks.add(track)
