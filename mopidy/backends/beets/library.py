from __future__ import unicode_literals

import logging

from mopidy import settings
from mopidy.backends import base
from mopidy.models import SearchResult

from .client import BeetsRemoteClient

logger = logging.getLogger('mopidy.backends.beets')


class BeetsLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(BeetsLibraryProvider, self).__init__(*args, **kwargs)
        self.remote = BeetsRemoteClient(settings.BEETS_SERVER_URI)

    def find_exact(self, **query):
        return self.search(**query)

    def search(self, **query):
        self._validate_query(query)
        if not query:
            return SearchResult(uri='beets:search', tracks=self.remote.get_tracks()) 

        for (field, values) in query.iteritems():
            if field == "album":
                return SearchResult(uri='beets:search', tracks=self.remote.get_album_by(values[0])) 
            if field == "artist":
                return SearchResult(uri='beets:search', tracks=self.remote.get_item_by(values[0]))
            if field == "any":
                return SearchResult(uri='beets:search', tracks=self.remote.get_item_by(values[0])) 

    def _validate_query(self, query):
        for (_, values) in query.iteritems():
            if not values:
                raise LookupError('Missing query')
            for value in values:
                if not value:
                    raise LookupError('Missing query')