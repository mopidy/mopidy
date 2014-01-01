from __future__ import unicode_literals

import gzip
import json
import logging
import os
import tempfile

import mopidy
from mopidy import models
from mopidy.backends import base
from mopidy.backends.local import search

logger = logging.getLogger(__name__)


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


class LocalJsonLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(LocalJsonLibraryProvider, self).__init__(*args, **kwargs)
        self._uri_mapping = {}
        self._media_dir = self.backend.config['local']['media_dir']
        self._json_file = self.backend.config['local-json']['json_file']
        self.refresh()

    def refresh(self, uri=None):
        logger.debug(
            'Loading local tracks from %s using %s',
            self._media_dir, self._json_file)

        tracks = load_library(self._json_file).get('tracks', [])
        uris_to_remove = set(self._uri_mapping)

        for track in tracks:
            self._uri_mapping[track.uri] = track
            uris_to_remove.discard(track.uri)

        for uri in uris_to_remove:
            del self._uri_mapping[uri]

        logger.info(
            'Loaded %d local tracks from %s using %s',
            len(tracks), self._media_dir, self._json_file)

    def lookup(self, uri):
        try:
            return [self._uri_mapping[uri]]
        except KeyError:
            logger.debug('Failed to lookup %r', uri)
            return []

    def find_exact(self, query=None, uris=None):
        tracks = self._uri_mapping.values()
        return search.find_exact(tracks, query=query, uris=uris)

    def search(self, query=None, uris=None):
        tracks = self._uri_mapping.values()
        return search.search(tracks, query=query, uris=uris)


class LocalJsonLibraryUpdateProvider(base.BaseLibraryProvider):
    uri_schemes = ['local']

    def __init__(self, config):
        self._tracks = {}
        self._media_dir = config['local']['media_dir']
        self._json_file = config['local-json']['json_file']

    def load(self):
        for track in load_library(self._json_file).get('tracks', []):
            self._tracks[track.uri] = track
        return self._tracks.values()

    def add(self, track):
        self._tracks[track.uri] = track

    def remove(self, uri):
        if uri in self._tracks:
            del self._tracks[uri]

    def commit(self):
        write_library(self._json_file, {'tracks': self._tracks.values()})
