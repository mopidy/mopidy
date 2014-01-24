from __future__ import absolute_import, unicode_literals

import collections
import gzip
import json
import logging
import os
import re
import sys
import tempfile
import time

import mopidy
from mopidy import local, models
from mopidy.local import search, translator

logger = logging.getLogger(__name__)


# TODO: move to load and dump in models?
def load_library(json_file):
    try:
        with gzip.open(json_file, 'rb') as fp:
            return json.load(fp, object_hook=models.model_json_decoder)
    except (IOError, ValueError) as e:
        logger.warning('Loading JSON local library failed: %s', e)
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
        # TODO: local.ROOT_DIRECTORY_URI
        self._cache = {'local:directory': collections.OrderedDict()}

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
                directory = '/'.join(parts[:i+1])
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
                    self._cache['local:directory'][child.uri] = child
                # If no parent was set we belong in the root.
                if not parent_uri:
                    parent_uri = 'local:directory'

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
        self._tracks = {}
        self._browse_cache = None
        self._media_dir = config['local']['media_dir']
        self._json_file = os.path.join(
            config['local']['data_dir'], b'library.json.gz')

    def browse(self, uri):
        if not self._browse_cache:
            return []
        return self._browse_cache.lookup(uri)

    def load(self):
        logger.debug('Loading library: %s', self._json_file)
        with DebugTimer('Loading tracks'):
            library = load_library(self._json_file)
            self._tracks = dict((t.uri, t) for t in library.get('tracks', []))
        with DebugTimer('Building browse cache'):
            self._browse_cache = _BrowseCache(sorted(self._tracks.keys()))
        return len(self._tracks)

    def lookup(self, uri):
        try:
            return self._tracks[uri]
        except KeyError:
            return None

    def search(self, query=None, limit=100, offset=0, uris=None, exact=False):
        tracks = self._tracks.values()
        # TODO: pass limit and offset into search helpers
        if exact:
            return search.find_exact(tracks, query=query, uris=uris)
        else:
            return search.search(tracks, query=query, uris=uris)

    def begin(self):
        return self._tracks.itervalues()

    def add(self, track):
        self._tracks[track.uri] = track

    def remove(self, uri):
        self._tracks.pop(uri, None)

    def close(self):
        write_library(self._json_file, {'tracks': self._tracks.values()})

    def clear(self):
        try:
            os.remove(self._json_file)
            return True
        except OSError:
            return False
