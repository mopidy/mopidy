from __future__ import unicode_literals

import logging
import os
import tempfile

from mopidy.backends import base
from mopidy.frontends.mpd import translator as mpd_translator
from mopidy.models import Album, SearchResult

from .translator import local_to_file_uri, parse_mpd_tag_cache

logger = logging.getLogger('mopidy.backends.local')


class LocalLibraryProvider(base.BaseLibraryProvider):
    def __init__(self, *args, **kwargs):
        super(LocalLibraryProvider, self).__init__(*args, **kwargs)
        self._uri_mapping = {}
        self._media_dir = self.backend.config['local']['media_dir']
        self._tag_cache_file = self.backend.config['local']['tag_cache_file']
        self.refresh()

    def _convert_to_int(self, string):
        try:
            return int(string)
        except ValueError:
            return object()

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
                if field == 'track_no':
                    q = self._convert_to_int(value)
                else:
                    q = value.strip()

                uri_filter = lambda t: q == t.uri
                track_name_filter = lambda t: q == t.name
                album_filter = lambda t: q == getattr(t, 'album', Album()).name
                artist_filter = lambda t: filter(
                    lambda a: q == a.name, t.artists)
                albumartist_filter = lambda t: any([
                    q == a.name
                    for a in getattr(t.album, 'artists', [])])
                composer_filter = lambda t: any([
                    q == a.name
                    for a in getattr(t, 'composers', [])])
                performer_filter = lambda t: any([
                    q == a.name
                    for a in getattr(t, 'performers', [])])
                track_no_filter = lambda t: q == t.track_no
                genre_filter = lambda t: t.genre and q == t.genre
                date_filter = lambda t: q == t.date
                comment_filter = lambda t: q == t.comment
                any_filter = lambda t: (
                    uri_filter(t) or
                    track_name_filter(t) or
                    album_filter(t) or
                    artist_filter(t) or
                    albumartist_filter(t) or
                    composer_filter(t) or
                    performer_filter(t) or
                    track_no_filter(t) or
                    genre_filter(t) or
                    date_filter(t) or
                    comment_filter(t))

                if field == 'uri':
                    result_tracks = filter(uri_filter, result_tracks)
                elif field == 'track_name':
                    result_tracks = filter(track_name_filter, result_tracks)
                elif field == 'album':
                    result_tracks = filter(album_filter, result_tracks)
                elif field == 'artist':
                    result_tracks = filter(artist_filter, result_tracks)
                elif field == 'albumartist':
                    result_tracks = filter(albumartist_filter, result_tracks)
                elif field == 'composer':
                    result_tracks = filter(composer_filter, result_tracks)
                elif field == 'performer':
                    result_tracks = filter(performer_filter, result_tracks)
                elif field == 'track_no':
                    result_tracks = filter(track_no_filter, result_tracks)
                elif field == 'genre':
                    result_tracks = filter(genre_filter, result_tracks)
                elif field == 'date':
                    result_tracks = filter(date_filter, result_tracks)
                elif field == 'comment':
                    result_tracks = filter(comment_filter, result_tracks)
                elif field == 'any':
                    result_tracks = filter(any_filter, result_tracks)
                else:
                    raise LookupError('Invalid lookup field: %s' % field)
        # TODO: add local:search:<query>
        return SearchResult(uri='local:search', tracks=result_tracks)

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
                if field == 'track_no':
                    q = self._convert_to_int(value)
                else:
                    q = value.strip().lower()

                uri_filter = lambda t: q in t.uri.lower()
                track_name_filter = lambda t: q in t.name.lower()
                album_filter = lambda t: q in getattr(
                    t, 'album', Album()).name.lower()
                artist_filter = lambda t: filter(
                    lambda a: q in a.name.lower(), t.artists)
                albumartist_filter = lambda t: any([
                    q in a.name.lower()
                    for a in getattr(t.album, 'artists', [])])
                composer_filter = lambda t: any([
                    q in a.name.lower()
                    for a in getattr(t, 'composers', [])])
                performer_filter = lambda t: any([
                    q in a.name.lower()
                    for a in getattr(t, 'performers', [])])
                track_no_filter = lambda t: q == t.track_no
                genre_filter = lambda t: t.genre and q in t.genre.lower()
                date_filter = lambda t: t.date and t.date.startswith(q)
                comment_filter = lambda t: t.comment and q in t.comment.lower()
                any_filter = lambda t: (
                    uri_filter(t) or
                    track_name_filter(t) or
                    album_filter(t) or
                    artist_filter(t) or
                    albumartist_filter(t) or
                    composer_filter(t) or
                    performer_filter(t) or
                    track_no_filter(t) or
                    genre_filter(t) or
                    date_filter(t) or
                    comment_filter(t))

                if field == 'uri':
                    result_tracks = filter(uri_filter, result_tracks)
                elif field == 'track_name':
                    result_tracks = filter(track_name_filter, result_tracks)
                elif field == 'album':
                    result_tracks = filter(album_filter, result_tracks)
                elif field == 'artist':
                    result_tracks = filter(artist_filter, result_tracks)
                elif field == 'albumartist':
                    result_tracks = filter(albumartist_filter, result_tracks)
                elif field == 'composer':
                    result_tracks = filter(composer_filter, result_tracks)
                elif field == 'performer':
                    result_tracks = filter(performer_filter, result_tracks)
                elif field == 'track_no':
                    result_tracks = filter(track_no_filter, result_tracks)
                elif field == 'genre':
                    result_tracks = filter(genre_filter, result_tracks)
                elif field == 'date':
                    result_tracks = filter(date_filter, result_tracks)
                elif field == 'comment':
                    result_tracks = filter(comment_filter, result_tracks)
                elif field == 'any':
                    result_tracks = filter(any_filter, result_tracks)
                else:
                    raise LookupError('Invalid lookup field: %s' % field)
        # TODO: add local:search:<query>
        return SearchResult(uri='local:search', tracks=result_tracks)

    def _validate_query(self, query):
        for (_, values) in query.iteritems():
            if not values:
                raise LookupError('Missing query')
            for value in values:
                if not value:
                    raise LookupError('Missing query')


# TODO: rename and move to tagcache extension.
class LocalLibraryUpdateProvider(base.BaseLibraryProvider):
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
            for row in mpd_translator.tracks_to_tag_cache_format(
                    self._tracks.values(), self._media_dir):
                if len(row) == 1:
                    tmp.write(('%s\n' % row).encode('utf-8'))
                else:
                    tmp.write(('%s: %s\n' % row).encode('utf-8'))

            os.rename(tmp.name, self._tag_cache_file)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
