from __future__ import unicode_literals

import logging

from mopidy.backends import base

logger = logging.getLogger('mopidy.backends.local')


class LocalLibraryProvider(base.BaseLibraryProvider):
    """Proxy library that delegates work to our active local library."""
    def __init__(self, backend, library):
        super(LocalLibraryProvider, self).__init__(backend)
        self._library = library
        self.refresh()

    def refresh(self, uri=None):
        if not self._library:
            return 0
        num_tracks = self._library.load()
        logger.info('Loaded %d local tracks using %s',
                    num_tracks, self._library.name)

    def lookup(self, uri):
        if not self._library:
            return []
        return self._library.lookup(uri)

    def find_exact(self, query=None, uris=None):
        if not self._library:
            return None
        return self._library.search(query=query, uris=uris, exact=True)

    def search(self, query=None, uris=None):
        if not self._library:
            return None
        return self._library.search(query=query, uris=uris, exact=False)
