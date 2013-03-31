from __future__ import unicode_literals

import logging
import urllib

from pymongo import MongoClient

from mopidy.models import Track, Artist, Album
from mopidy.utils.encoding import locale_decode
from mopidy.utils.path import path_to_uri

logger = logging.getLogger('mopidy.backends.mongodb')

def convert_mongo_doc_to_track( data, music_dir = '' ):
    if not data:
        raise Exception( 'No data provided to create track' )

    # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
    # See https://github.com/mopidy/mopidy/issues/302 for details.

    track_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    albumartist_kwargs = {}

    if 'Track' in data:
        if type( data['Track'] ) is list:
            album_kwargs[b'num_tracks'] = data[ 'Track' ][ 1 ]
            track_kwargs[b'track_no'] = data[ 'Track' ][ 0 ]
        else:
            track_kwargs[b'track_no'] = data[ 'Track' ]

    if 'Artist' in data:
        artist_kwargs[b'name'] = data['Artist']
        albumartist_kwargs[b'name'] = data['Artist']
    else:
        artist_kwargs[b'name'] = "Unknown Artist"

    if 'AlbumArtist' in data:
        albumartist_kwargs[b'name'] = data['AlbumArtist']

    if "name" not in albumartist_kwargs:
        albumartist_kwargs[b'name'] = "Unknown Artist"

    if 'Album' in data:
        album_kwargs[b'name'] = data['Album']

    if 'Title' in data:
        track_kwargs[b'name'] = data['Title']

    if 'Year' in data:
        track_kwargs[b'date'] = str( data['Year'] )

    if 'MUSICBRAINZ_TRACKID' in data:
        track_kwargs[b'musicbrainz_id'] = data['MUSICBRAINZ_TRACKID']

    if 'MUSICBRAINZ_ALBUMID' in data:
        album_kwargs[b'musicbrainz_id'] = data['MUSICBRAINZ_ALBUMID']

    if 'MUSICBRAINZ_ARTISTID' in data:
        artist_kwargs[b'musicbrainz_id'] = data['MUSICBRAINZ_ARTISTID']

    if 'MUSICBRAINZ_ALBUMARTISTID' in data:
        albumartist_kwargs[b'musicbrainz_id'] = (
            data['MUSICBRAINZ_ALBUMARTISTID'])

    if data['file'][0] == '/':
        path = data['file'][1:]
    else:
        path = data['file']
    path = urllib.unquote(path)

    if artist_kwargs:
        artist = Artist(**artist_kwargs)
        track_kwargs[b'artists'] = [artist]

    if albumartist_kwargs:
        albumartist = Artist(**albumartist_kwargs)
        album_kwargs[b'artists'] = [albumartist]

    if album_kwargs:
        album = Album(**album_kwargs)
        track_kwargs[b'album'] = album

    track_kwargs[b'uri'] = path_to_uri(music_dir, path)
    track_kwargs[b'length'] = int(data.get('Time', 0)) * 1000

    return Track(**track_kwargs)
