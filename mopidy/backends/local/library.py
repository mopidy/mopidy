from __future__ import unicode_literals

import logging
import os

from mopidy.backends import base
from mopidy.models import Album, SearchResult
from mopidy.utils.encoding import locale_decode

from .translator import parse_mpd_tag_cache

logger = logging.getLogger('mopidy.backends.local')


class LocalLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(LocalLibraryProvider, self).__init__(*args, **kwargs)
        self._uri_mapping = {}
        self._media_dir = self.backend.config['local']['media_dir']
        self._tag_cache_file = self.backend.config['local']['tag_cache_file']
        self.refresh()

    def refresh(self, uri=None):
        try:
            if not os.path.exists(self._tag_cache_file):
                basedir = os.path.dirname(self._tag_cache_file)
                if not os.path.exists(basedir):
                    os.makedirs(basedir)
                open(self._tag_cache_file, 'a').close()
        except IOError as error:
            logger.warning(
                'Could not create empty tag cache: %s', locale_decode(error))
            return

        logger.info(
            'Loading tracks from %s using %s',
            self._media_dir, self._tag_cache_file)

        tracks = parse_mpd_tag_cache(self._tag_cache_file, self._media_dir)

        for track in tracks:
            self._uri_mapping[track.uri] = track

    def lookup(self, uri):
        try:
            return [self._uri_mapping[uri]]
        except KeyError:
            logger.debug('Failed to lookup %r', uri)
            return []

    def find_exact(self, query=None, uris=None):
        # TODO Only return results within URI roots given by ``uris``

        if query is None:
            query = {}
        self._validate_query(query)
        result_tracks = self._uri_mapping.values()

        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]
            # FIXME this is bound to be slow for large libraries
            for value in values:
                q = value.strip()

                uri_filter = lambda t: q == t.uri
                track_filter = lambda t: q == t.name
                album_filter = lambda t: q == getattr(t, 'album', Album()).name
                artist_filter = lambda t: filter(
                    lambda a: q == a.name, t.artists)
                date_filter = lambda t: q == t.date
                any_filter = lambda t: (
                    track_filter(t) or album_filter(t) or
                    artist_filter(t) or uri_filter(t))

                if field == 'uri':
                    result_tracks = filter(uri_filter, result_tracks)
                elif field == 'track':
                    result_tracks = filter(track_filter, result_tracks)
                elif field == 'album':
                    result_tracks = filter(album_filter, result_tracks)
                elif field == 'artist':
                    result_tracks = filter(artist_filter, result_tracks)
                elif field == 'date':
                    result_tracks = filter(date_filter, result_tracks)
                elif field == 'any':
                    result_tracks = filter(any_filter, result_tracks)
                else:
                    raise LookupError('Invalid lookup field: %s' % field)
        return SearchResult(uri='file:search', tracks=result_tracks)

    def search(self, query=None, uris=None):
        # TODO Only return results within URI roots given by ``uris``

        if query is None:
            query = {}
        self._validate_query(query)
        result_tracks = self._uri_mapping.values()

        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]
            # FIXME this is bound to be slow for large libraries
            for value in values:
                q = value.strip().lower()

                uri_filter = lambda t: q in t.uri.lower()
                track_filter = lambda t: q in t.name.lower()
                album_filter = lambda t: q in getattr(
                    t, 'album', Album()).name.lower()
                artist_filter = lambda t: filter(
                    lambda a: q in a.name.lower(), t.artists)
                date_filter = lambda t: t.date and t.date.startswith(q)
                any_filter = lambda t: track_filter(t) or album_filter(t) or \
                    artist_filter(t) or uri_filter(t)

                if field == 'uri':
                    result_tracks = filter(uri_filter, result_tracks)
                elif field == 'track':
                    result_tracks = filter(track_filter, result_tracks)
                elif field == 'album':
                    result_tracks = filter(album_filter, result_tracks)
                elif field == 'artist':
                    result_tracks = filter(artist_filter, result_tracks)
                elif field == 'date':
                    result_tracks = filter(date_filter, result_tracks)
                elif field == 'any':
                    result_tracks = filter(any_filter, result_tracks)
                else:
                    raise LookupError('Invalid lookup field: %s' % field)
        return SearchResult(uri='file:search', tracks=result_tracks)

    def _validate_query(self, query):
        for (_, values) in query.iteritems():
            if not values:
                raise LookupError('Missing query')
            for value in values:
                if not value:
                    raise LookupError('Missing query')
