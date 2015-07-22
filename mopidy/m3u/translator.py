from __future__ import absolute_import, unicode_literals

import codecs
import logging
import os
import re
import urllib
import urlparse

from mopidy import compat
from mopidy.internal import encoding, path
from mopidy.models import Track


M3U_EXTINF_RE = re.compile(r'#EXTINF:(-1|\d+),(.*)')

logger = logging.getLogger(__name__)


def playlist_uri_to_path(uri, playlists_dir):
    if not uri.startswith('m3u:'):
        raise ValueError('Invalid URI %s' % uri)
    file_path = path.uri_to_path(uri)
    return os.path.join(playlists_dir, file_path)


def path_to_playlist_uri(relpath):
    """Convert path relative to playlists_dir to M3U URI."""
    if isinstance(relpath, compat.text_type):
        relpath = relpath.encode('utf-8')
    return b'm3u:%s' % urllib.quote(relpath)


def m3u_extinf_to_track(line):
    """Convert extended M3U directive to track template."""
    m = M3U_EXTINF_RE.match(line)
    if not m:
        logger.warning('Invalid extended M3U directive: %s', line)
        return Track()
    (runtime, title) = m.groups()
    if int(runtime) > 0:
        return Track(name=title, length=1000 * int(runtime))
    else:
        return Track(name=title)


def parse_m3u(file_path, media_dir=None):
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
        logger.warning('Couldn\'t open m3u: %s', encoding.locale_decode(error))
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
            tracks.append(track.replace(uri=line))
        elif os.path.normpath(line) == os.path.abspath(line):
            uri = path.path_to_uri(line)
            tracks.append(track.replace(uri=uri))
        elif media_dir is not None:
            uri = path.path_to_uri(os.path.join(media_dir, line))
            tracks.append(track.replace(uri=uri))

        track = Track()
    return tracks


def save_m3u(filename, tracks, encoding='latin1', errors='replace'):
    extended = any(track.name for track in tracks)
    # codecs.open() always uses binary mode, just being explicit here
    with codecs.open(filename, 'wb', encoding, errors) as m3u:
        if extended:
            m3u.write('#EXTM3U' + os.linesep)
        for track in tracks:
            if extended and track.name:
                m3u.write('#EXTINF:%d,%s%s' % (
                    track.length // 1000 if track.length else -1,
                    track.name,
                    os.linesep))
            m3u.write(track.uri + os.linesep)
