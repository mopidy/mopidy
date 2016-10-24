from __future__ import absolute_import, absolute_import, unicode_literals

import collections
import logging
import os
import re
import sys

import mopidy

from mopidy import compat, local, models
from mopidy.internal import storage as internal_storage
from mopidy.internal import timer
from mopidy.local import search, storage, translator


logger = logging.getLogger(__name__)


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
            track_ref = models.Ref.track(uri=track_uri, name=parts.pop())

            # Look for our parents backwards as this is faster than having to
            # do a complete search for each add.
            parent_uri = None
            child = None
            for i in reversed(range(len(parts))):
                directory = '/'.join(parts[:i + 1])
                uri = translator.path_to_local_directory_uri(directory)

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
                # Loop completed, so final child needs to be added to root.
                if child:
                    self._cache[
                        local.Library.ROOT_DIRECTORY_URI][child.uri] = child
                # If no parent was set we belong in the root.
                if not parent_uri:
                    parent_uri = local.Library.ROOT_DIRECTORY_URI

            self._cache[parent_uri][track_uri] = track_ref

    def lookup(self, uri):
        return self._cache.get(uri, {}).values()


class JsonLibrary(local.Library):
    name = 'json'

    def __init__(self, config):
        self._tracks = {}
        self._browse_cache = None
        self._media_dir = config['local']['media_dir']
        self._json_file = os.path.join(
            local.Extension.get_data_dir(config), b'library.json.gz')

        storage.check_dirs_and_files(config)

    def browse(self, uri):
        if not self._browse_cache:
            return []
        return self._browse_cache.lookup(uri)

    def load(self):
        logger.debug('Loading library: %s', self._json_file)
        with timer.time_logger('Loading tracks'):
            if not os.path.isfile(self._json_file):
                logger.info(
                    'No local library metadata cache found at %s. Please run '
                    '`mopidy local scan` to index your local music library. '
                    'If you do not have a local music collection, you can '
                    'disable the local backend to hide this message.',
                    self._json_file)
                self._tracks = {}
            else:
                library = internal_storage.load(self._json_file)
                self._tracks = dict((t.uri, t) for t in
                                    library.get('tracks', []))
        with timer.time_logger('Building browse cache'):
            self._browse_cache = _BrowseCache(sorted(self._tracks.keys()))
        return len(self._tracks)

    def lookup(self, uri):
        try:
            return [self._tracks[uri]]
        except KeyError:
            return []

    def get_distinct(self, field, query=None):
        if field == 'track':
            def distinct(track):
                return {track.name}
        elif field == 'artist':
            def distinct(track):
                return {a.name for a in track.artists}
        elif field == 'albumartist':
            def distinct(track):
                album = track.album or models.Album()
                return {a.name for a in album.artists}
        elif field == 'album':
            def distinct(track):
                album = track.album or models.Album()
                return {album.name}
        elif field == 'composer':
            def distinct(track):
                return {a.name for a in track.composers}
        elif field == 'performer':
            def distinct(track):
                return {a.name for a in track.performers}
        elif field == 'date':
            def distinct(track):
                return {track.date}
        elif field == 'genre':
            def distinct(track):
                return {track.genre}
        else:
            return set()

        distinct_result = set()
        search_result = search.search(self._tracks.values(), query, limit=None)
        for track in search_result.tracks:
            distinct_result.update(distinct(track))
        return distinct_result - {None}

    def search(self, query=None, limit=100, offset=0, uris=None, exact=False):
        tracks = self._tracks.values()
        if exact:
            return search.find_exact(
                tracks, query=query, limit=limit, offset=offset, uris=uris)
        else:
            return search.search(
                tracks, query=query, limit=limit, offset=offset, uris=uris)

    def begin(self):
        return compat.itervalues(self._tracks)

    def add(self, track):
        self._tracks[track.uri] = track

    def remove(self, uri):
        self._tracks.pop(uri, None)

    def close(self):
        internal_storage.dump(self._json_file, {
            'version': mopidy.__version__,
            'tracks': self._tracks.values()
        })

    def clear(self):
        try:
            os.remove(self._json_file)
            return True
        except OSError:
            return False
