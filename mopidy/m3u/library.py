from __future__ import absolute_import, unicode_literals

import logging

from mopidy import backend

logger = logging.getLogger(__name__)


class M3ULibraryProvider(backend.LibraryProvider):
    """Library for looking up M3U playlists."""

    def __init__(self, backend):
        super(M3ULibraryProvider, self).__init__(backend)

    def lookup(self, uri):
        # TODO Lookup tracks in M3U playlist
        return []
