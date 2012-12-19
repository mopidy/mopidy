from __future__ import unicode_literals

import logging

import pykka
from spotify import Link, SpotifyError

from mopidy import settings
from mopidy.backends import base
from mopidy.models import Track

from . import translator

logger = logging.getLogger('mopidy.backends.spotify')


class SpotifyTrack(Track):
    """Proxy object for unloaded Spotify tracks."""
    def __init__(self, uri):
        super(SpotifyTrack, self).__init__()
        self._spotify_track = Link.from_string(uri).as_track()
        self._unloaded_track = Track(uri=uri, name='[loading...]')
        self._track = None

    @property
    def _proxy(self):
        if self._track:
            return self._track
        elif self._spotify_track.is_loaded():
            self._track = translator.to_mopidy_track(self._spotify_track)
            return self._track
        else:
            return self._unloaded_track

    def __getattribute__(self, name):
        if name.startswith('_'):
            return super(SpotifyTrack, self).__getattribute__(name)
        return self._proxy.__getattribute__(name)

    def __repr__(self):
        return self._proxy.__repr__()

    def __hash__(self):
        return hash(self._proxy.uri)

    def __eq__(self, other):
        if not isinstance(other, Track):
            return False
        return self._proxy.uri == other.uri

    def copy(self, **values):
        return self._proxy.copy(**values)


class SpotifyLibraryProvider(base.BaseLibraryProvider):
    def find_exact(self, **query):
        return self.search(**query)

    def lookup(self, uri):
        try:
            return [SpotifyTrack(uri)]
        except SpotifyError as e:
            logger.debug('Failed to lookup "%s": %s', uri, e)
            return []

    def refresh(self, uri=None):
        pass  # TODO

    def search(self, **query):
        if not query:
            return self._get_all_tracks()

        spotify_query = self._translate_search_query(query)
        logger.debug('Spotify search query: %s' % spotify_query)

        future = pykka.ThreadingFuture()

        def callback(results, userdata=None):
            # TODO Include results from results.albums(), etc. too
            # TODO Consider launching a second search if results.total_tracks()
            # is larger than len(results.tracks())
            tracks = [
                translator.to_mopidy_track(t) for t in results.tracks()]
            future.set(tracks)

        if not self.backend.spotify.connected.wait(settings.SPOTIFY_TIMEOUT):
            logger.debug('Not connected: Spotify search cancelled')
            return []

        self.backend.spotify.session.search(
            spotify_query, callback,
            track_count=100, album_count=0, artist_count=0)

        try:
            return future.get(timeout=settings.SPOTIFY_TIMEOUT)
        except pykka.Timeout:
            logger.debug(
                'Timeout: Spotify search did not return in %ds',
                settings.SPOTIFY_TIMEOUT)
            return []

    def _get_all_tracks(self):
        # Since we can't search for the entire Spotify library, we return
        # all tracks in the playlists when the query is empty.
        tracks = []
        for playlist in self.backend.playlists.playlists:
            tracks += playlist.tracks
        return tracks

    def _translate_search_query(self, mopidy_query):
        spotify_query = []
        for (field, values) in mopidy_query.iteritems():
            if field == 'uri':
                tracks = []
                for value in values:
                    track = self.lookup(value)
                    if track:
                        tracks.append(track)
                return tracks
            elif field == 'track':
                field = 'title'
            elif field == 'date':
                field = 'year'
            if not hasattr(values, '__iter__'):
                values = [values]
            for value in values:
                if field == 'any':
                    spotify_query.append(value)
                elif field == 'year':
                    value = int(value.split('-')[0])  # Extract year
                    spotify_query.append('%s:%d' % (field, value))
                else:
                    spotify_query.append('%s:"%s"' % (field, value))
        spotify_query = ' '.join(spotify_query)
        return spotify_query
