from __future__ import unicode_literals

import logging
import os
import re
import urllib

from mopidy.frontends.mpd import translator as mpd, protocol
from mopidy.models import Track, Artist, Album
from mopidy.utils.encoding import locale_decode
from mopidy.utils.path import mtime as get_mtime, split_path, uri_to_path

logger = logging.getLogger('mopidy.backends.local.tagcache')


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
        track_result = dict(mpd.track_to_mpd_format(track))

        # XXX Don't save comments to the tag cache as they may span multiple
        # lines. We'll start saving track comments when we move from tag_cache
        # to a JSON file. See #579 for details.
        if 'Comment' in track_result:
            del track_result['Comment']

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


MPD_KEY_ORDER = '''
    key file Time Artist Album AlbumArtist Title Track Genre Date Composer
    Performer Comment Disc MUSICBRAINZ_ALBUMID MUSICBRAINZ_ALBUMARTISTID
    MUSICBRAINZ_ARTISTID MUSICBRAINZ_TRACKID mtime
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
