from __future__ import absolute_import, absolute_import, unicode_literals

import collections
import gzip
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
import time
from urllib import unquote_plus


import mopidy
from mopidy import compat, local, models
from mopidy.local import search, storage, translator
from mopidy.utils import encoding

logger = logging.getLogger(__name__)


# TODO: move to load and dump in models?
def load_library(json_file):
    if not os.path.isfile(json_file):
        logger.info(
            'No local library metadata cache found at %s. Please run '
            '`mopidy local scan` to index your local music library. '
            'If you do not have a local music collection, you can disable the '
            'local backend to hide this message.',
            json_file)
        return {}
    try:
        with gzip.open(json_file, 'rb') as fp:
            return json.load(
                fp, object_hook=models.model_json_decoder)
    except (IOError, ValueError) as error:
        logger.warning(
            'Loading JSON local library failed: %s',
            encoding.locale_decode(error))
        return {}


def write_library(json_file, data):
    data['version'] = mopidy.__version__
    directory, basename = os.path.split(json_file)

    # TODO: cleanup directory/basename.* files.
    tmp = tempfile.NamedTemporaryFile(
        prefix=basename + '.', dir=directory, delete=False)

    try:
        with gzip.GzipFile(fileobj=tmp, mode='wb') as fp:
            json.dump(data, fp, cls=models.ModelJSONEncoder,
                      indent=2, separators=(',', ': '))
        os.rename(tmp.name, json_file)
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


class _BrowseCache(object):
    encoding = sys.getfilesystemencoding()
    splitpath_re = re.compile(r'([^/]+)')

    def __init__(self, uris):
        self._cache = {
            local.Library.ROOT_DIRECTORY_URI: collections.OrderedDict()}

        for track_uri in uris:
            path = translator.local_track_uri_to_path(track_uri, b'/')
            parts = self.splitpath_re.findall(
                path.decode(self.encoding, 'replace'))
            track_ref = models.Ref.track(
                uri=track_uri,
                name=parts.pop())

            # Look for our parents backwards as this is faster than having to
            # do a complete search for each add.
            parent_uri = None
            child = None
            for i in reversed(range(len(parts))):
                directory = '/'.join(parts[:i + 1])
                uri = translator.path_to_local_directory_uri(
                    directory)

                # First dir we process is our parent
                if not parent_uri:
                    parent_uri = uri

                # We found ourselves and we exist, done.
                if uri in self._cache:
                    if child:
                        self._cache[uri][child.uri] = child
                    break

                # Initialize ourselves, store child if present, and add
                # ourselves as child for next loop.
                self._cache[uri] = collections.OrderedDict()
                if child:
                    self._cache[uri][child.uri] = child
                child = models.Ref.directory(uri=uri, name=parts[i])
            else:
                # Loop completed, so final child needs to be added to
                # root.
                if child:
                    self._cache[
                        local.Library.ROOT_DIRECTORY_URI][child.uri] = child
                # If no parent was set we belong in the root.
                if not parent_uri:
                    parent_uri = local.Library.ROOT_DIRECTORY_URI

            self._cache[parent_uri][track_uri] = track_ref

    def lookup(self, uri):
        return self._cache.get(uri, {}).values()


# TODO: make this available to other code?
class DebugTimer(object):

    def __init__(self, msg):
        self.msg = msg
        self.start = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_value, traceback):
        duration = (time.time() - self.start) * 1000
        logger.debug('%s: %dms', self.msg, duration)


class JsonLibrary(local.Library):
    name = 'json'

    def __init__(self, config):
        self._trackdb = sqlite3.connect(
            ":memory:",
            check_same_thread=False)
        self._trackdb.row_factory = sqlite3.Row
        cur = self._trackdb.cursor()
        cur.execute(
            "create table tracks "
            "(uri text COLLATE NOCASE,"
            " name text COLLATE NOCASE,"
            " album_name text COLLATE NOCASE,"
            " artist_name text COLLATE NOCASE,"
            " date text,"
            " genre text COLLATE NOCASE,"
            " last_modified integer,"
            " length integer,"
            " track_no integer,"
            " num_tracks integer,"
            " composer text COLLATE NOCASE,"
            " performer text COLLATE NOCASE,"
            " album_artist text COLLATE NOCASE,"
            " comment text COLLATE NOCASE)")
        cur.execute(
            "create index tracks_album_name on tracks(album_name)")
        cur.execute(
            "create index tracks_artist_name on tracks(artist_name)")
        cur.execute(
            "create index tracks_album_name_artist_name_date "
            "on tracks(artist_name,album_name)")
        self._trackdb.commit()
        self._tracks = {}
        self._albums = {}
        self._artists = {}
        self._browse_cache = None
        self._media_dir = config['local']['media_dir']
        self._json_file = os.path.join(
            config['local']['data_dir'], b'library.json.gz')

        storage.check_dirs_and_files(config)

    def browse(self, uri):
        if not self._browse_cache:
            return []
        return self._browse_cache.lookup(uri)

    def load(self):
        logger.debug('Loading library: %s', self._json_file)
        with DebugTimer('Loading tracks'):
            library = load_library(self._json_file)
            self._tracks = dict(
                (t.uri,
                 t) for t in library.get(
                    'tracks',
                    []))
            cur = self._trackdb.cursor()
            for track in self._tracks.values():
                if len(track.artists):
                    track_artist = list(track.artists)[0].name
                else:
                    track_artist = None
                if len(track.album.artists) > 0:
                    album_artist = list(track.album.artists)[0].name
                elif len(track.artists):
                    album_artist = list(track.artists)[0].name
                elif len(track.composers):
                    album_artist = list(track.composers)[0].name
                elif len(track.performers):
                    album_artist = list(track.performers)[0].name
                else:
                    album_artist = None
                if len(track.composers) > 0:
                    composer = list(track.composers)[0].name
                else:
                    composer = None
                if len(track.performers) > 0:
                    performer = list(track.performers)[0].name
                else:
                    performer = None
                cur.execute("insert into tracks("
                            "uri,name,album_name,artist_name,date,genre, "
                            "last_modified,length,track_no,num_tracks, "
                            "composer,performer,album_artist,comment) "
                            "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                                track.uri, track.name, track.album.name,
                                track_artist, track.date, track.genre,
                                track.last_modified, track.length,
                                track.track_no, track.album.num_tracks,
                                composer, performer, album_artist,
                                track.comment))
            self._trackdb.commit()
        with DebugTimer('Building browse cache'):
            self._browse_cache = _BrowseCache(
                sorted(
                    self._tracks.keys()))
        return len(self._tracks)

    def splitURI(self, uri, testURI):
        if uri.startswith(testURI):
            returnVal = uri[len(testURI):]
            returnVal = unquote_plus(returnVal)
            return returnVal
        else:
            return None

    def lookup(self, uri):
        artistName = self.splitURI(
            uri,
            u"local:directory:type=artist/")
        if artistName is not None:
            if artistName.find("/") != -1:
                (artistName, albumName) = artistName.split("/")[0:2]
                tracks = self.advanced_search(
                    {"artist": [artistName], "album": [albumName]},
                    exact=True, returnType=models.Track).tracks
            else:
                tracks = self.advanced_search(
                    {"artist": [artistName]},
                    exact=True, returnType=models.Track).tracks
            return tracks
        try:
            return [self._tracks[uri]]
        except KeyError:
            return []

    def search(
            self, query=None, limit=100, offset=0, uris=None, exact=False):
        return search.advanced_search_sql(
            self._trackdb, query=query, uris=uris,
            exact=exact, returnType=models.Track,
            limit=limit, offset=offset)

    def advanced_search(self, query=None, uris=None, exact=False,
                        returnType=models.Track, limit=0, offset=0, **kwargs):
        return search.advanced_search_sql(
            self._trackdb, query, uris, exact, returnType, limit, offset)

    def begin(self):
        return compat.itervalues(self._tracks)

    def add(self, track):
        self._tracks[track.uri] = track

    def remove(self, uri):
        self._tracks.pop(uri, None)

    def close(self):
        write_library(
            self._json_file, {
                'tracks': self._tracks.values()})

    def clear(self):
        try:
            os.remove(self._json_file)
            return True
        except OSError:
            return False
