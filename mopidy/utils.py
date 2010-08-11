import logging
import os
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

def import_module(name):
    __import__(name)
    return sys.modules[name]

def get_class(name):
    module_name = name[:name.rindex('.')]
    class_name = name[name.rindex('.') + 1:]
    logger.debug('Loading: %s', name)
    module = import_module(module_name)
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
    #path = os.path.expanduser(path) # FIXME
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
        path = data['file'][1:]
    else:
        path = data['file']

    track_kwargs['uri'] = path_to_uri(music_dir, path)
    track_kwargs['length'] = int(data.get('time', 0)) * 1000

    track = Track(**track_kwargs)
    tracks.add(track)
