from __future__ import absolute_import, unicode_literals

import logging

from mopidy import backend, local, models

logger = logging.getLogger(__name__)


class LocalLibraryProvider(backend.LibraryProvider):

    """Proxy library that delegates work to our active local library."""

    root_directory = models.Ref.directory(
        uri=local.Library.ROOT_DIRECTORY_URI, name='Local media')

    def __init__(self, backend, library):
        super(LocalLibraryProvider, self).__init__(backend)
        self._library = library
        self.refresh()

    def browse(self, uri):
        if not self._library:
            return []
        return self._library.browse(uri)

    def get_distinct(self, field, query=None):
        if not self._library:
            return set()
        return self._library.get_distinct(field, query)

    def get_images(self, uris):
        if not self._library:
            return {}
        return self._library.get_images(uris)

    def refresh(self, uri=None):
        if not self._library:
            return 0
        num_tracks = self._library.load()
        logger.info('Loaded %d local tracks using %s',
                    num_tracks, self._library.name)

    def lookup(self, uri):
        if not self._library:
            return []
        tracks = self._library.lookup(uri)
        if tracks is None:
            logger.debug('Failed to lookup %r', uri)
            return []
        if isinstance(tracks, models.Track):
            tracks = [tracks]
        return tracks

    def search(self, query=None, uris=None, exact=False):
        if not self._library:
            return None
        return self._library.search(query=query, uris=uris, exact=exact)
