from __future__ import unicode_literals

import logging
import os
import tempfile

from mopidy.backends import base
from mopidy.backends.local.translator import local_to_file_uri
from mopidy.backends.local import search

from .translator import parse_mpd_tag_cache, tracks_to_tag_cache_format

logger = logging.getLogger('mopidy.backends.local.tagcache')


class LocalTagcacheLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(LocalTagcacheLibraryProvider, self).__init__(*args, **kwargs)
        self._uri_mapping = {}
        self._media_dir = self.backend.config['local']['media_dir']
        self._tag_cache_file = self.backend.config['local']['tag_cache_file']
        self.refresh()

    def refresh(self, uri=None):
        logger.debug(
            'Loading local tracks from %s using %s',
            self._media_dir, self._tag_cache_file)

        tracks = parse_mpd_tag_cache(self._tag_cache_file, self._media_dir)
        uris_to_remove = set(self._uri_mapping)

        for track in tracks:
            self._uri_mapping[track.uri] = track
            uris_to_remove.discard(track.uri)

        for uri in uris_to_remove:
            del self._uri_mapping[uri]

        logger.info(
            'Loaded %d local tracks from %s using %s',
            len(tracks), self._media_dir, self._tag_cache_file)

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


class LocalTagcacheLibraryUpdateProvider(base.BaseLibraryProvider):
    uri_schemes = ['local']

    def __init__(self, config):
        self._tracks = {}
        self._media_dir = config['local']['media_dir']
        self._tag_cache_file = config['local']['tag_cache_file']

    def load(self):
        tracks = parse_mpd_tag_cache(self._tag_cache_file, self._media_dir)
        for track in tracks:
            # TODO: this should use uris as is, i.e. hack that should go away
            # with tag caches.
            uri = local_to_file_uri(track.uri, self._media_dir)
            self._tracks[uri] = track.copy(uri=uri)
        return tracks

    def add(self, track):
        self._tracks[track.uri] = track

    def remove(self, uri):
        if uri in self._tracks:
            del self._tracks[uri]

    def commit(self):
        directory, basename = os.path.split(self._tag_cache_file)

        # TODO: cleanup directory/basename.* files.
        tmp = tempfile.NamedTemporaryFile(
            prefix=basename + '.', dir=directory, delete=False)

        try:
            for row in tracks_to_tag_cache_format(
                    self._tracks.values(), self._media_dir):
                if len(row) == 1:
                    tmp.write(('%s\n' % row).encode('utf-8'))
                else:
                    tmp.write(('%s: %s\n' % row).encode('utf-8'))

            os.rename(tmp.name, self._tag_cache_file)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
