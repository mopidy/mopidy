from __future__ import unicode_literals

import logging

from mopidy.backends import base
from mopidy.models import SearchResult

logger = logging.getLogger('mopidy.backends.soundcloud')


class SoundCloudLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(SoundCloudLibraryProvider, self).__init__(*args, **kwargs)

    def find_exact(self, **query):
        return self.search(**query)

    def search(self, **query):
        if not query:
            return

        for (field, val) in query.iteritems():

            # TODO: Devise method for searching SoundCloud via artists
            if field == "album" and query['album'] == "SoundCloud":
                return SearchResult(
                    uri='soundcloud:search',
                    tracks=self.backend.sc_api.search(query['artist']) or [])
            elif field == "any":
                return SearchResult(
                    uri='soundcloud:search',
                    tracks=self.backend.sc_api.search(val[0]) or [])
            else:
                return []

    def lookup(self, uri):
        try:
            id = uri.split('//')[1]
            logger.debug(u'SoundCloud track id for %s: %s' % (uri, id))
            return [self.backend.sc_api.get_track(id, True)]
        except Exception as error:
            logger.debug(u'Failed to lookup %s: %s', uri, error)
            return []
