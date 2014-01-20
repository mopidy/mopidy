from __future__ import unicode_literals

import logging
import os
import re
import urlparse
import urllib

from mopidy.models import Track
from mopidy.utils.encoding import locale_decode
from mopidy.utils.path import path_to_uri, uri_to_path

M3U_EXTINF_RE = re.compile(r'#EXTINF:(-1|\d+),(.*)')

logger = logging.getLogger(__name__)


def local_track_uri_to_file_uri(uri, media_dir):
    return path_to_uri(local_track_uri_to_path(uri, media_dir))


def local_track_uri_to_path(uri, media_dir):
    if not uri.startswith('local:track:'):
        raise ValueError('Invalid URI.')
    file_path = uri_to_path(uri).split(b':', 1)[1]
    return os.path.join(media_dir, file_path)


def path_to_local_track_uri(relpath):
    """Convert path releative to media_dir to local track URI."""
    if isinstance(relpath, unicode):
        relpath = relpath.encode('utf-8')
    return b'local:track:%s' % urllib.quote(relpath)


def path_to_local_directory_uri(relpath):
    """Convert path relative to :confval:`local/media_dir` directory URI."""
    if isinstance(relpath, unicode):
        relpath = relpath.encode('utf-8')
    return b'local:directory:%s' % urllib.quote(relpath)


def m3u_extinf_to_track(line):
    """Convert extended M3U directive to track template."""
    m = M3U_EXTINF_RE.match(line)
    if not m:
        logger.warning('Invalid extended M3U directive: %s', line)
        return Track()
    (runtime, title) = m.groups()
    if int(runtime) > 0:
        return Track(name=title, length=1000*int(runtime))
    else:
        return Track(name=title)


def parse_m3u(file_path, media_dir):
    r"""
    Convert M3U file list to list of tracks

    Example M3U data::

        # This is a comment
        Alternative\Band - Song.mp3
        Classical\Other Band - New Song.mp3
        Stuff.mp3
        D:\More Music\Foo.mp3
        http://www.example.com:8000/Listen.pls
        http://www.example.com/~user/Mine.mp3

    Example extended M3U data::

        #EXTM3U
        #EXTINF:123, Sample artist - Sample title
        Sample.mp3
        #EXTINF:321,Example Artist - Example title
        Greatest Hits\Example.ogg
        #EXTINF:-1,Radio XMP
        http://mp3stream.example.com:8000/

    - Relative paths of songs should be with respect to location of M3U.
    - Paths are normally platform specific.
    - Lines starting with # are ignored, except for extended M3U directives.
    - Track.name and Track.length are set from extended M3U directives.
    - m3u files are latin-1.
    """
    # TODO: uris as bytes
    tracks = []
    try:
        with open(file_path) as m3u:
            contents = m3u.readlines()
    except IOError as error:
        logger.warning('Couldn\'t open m3u: %s', locale_decode(error))
        return tracks

    if not contents:
        return tracks

    extended = contents[0].decode('latin1').startswith('#EXTM3U')

    track = Track()
    for line in contents:
        line = line.strip().decode('latin1')

        if line.startswith('#'):
            if extended and line.startswith('#EXTINF'):
                track = m3u_extinf_to_track(line)
            continue

        if urlparse.urlsplit(line).scheme:
            tracks.append(track.copy(uri=line))
        elif os.path.normpath(line) == os.path.abspath(line):
            path = path_to_uri(line)
            tracks.append(track.copy(uri=path))
        else:
            path = path_to_uri(os.path.join(media_dir, line))
            tracks.append(track.copy(uri=path))

        track = Track()
    return tracks
