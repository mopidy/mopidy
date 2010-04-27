import logging
from multiprocessing.reduction import reduce_connection
import os
import pickle
import urllib

logger = logging.getLogger('mopidy.utils')

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

def get_or_create_dotdir(dotdir):
    dotdir = os.path.expanduser(dotdir)
    if not os.path.isdir(dotdir):
        logger.info(u'Creating %s', dotdir)
        os.mkdir(dotdir, 0755)
    return dotdir

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

def m3u_to_uris(file_path):
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

    with open(file_path) as m3u:
        for line in m3u.readlines():
            line = line.strip().decode('latin1')

            if line.startswith('#'):
                continue

            if line.startswith('file://'):
                uris.append(line)
            else:
                file = os.path.join(folder, line)
                path = urllib.pathname2url(file.encode('utf-8'))
                uris.append('file://' + path)

    return uris
