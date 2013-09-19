from __future__ import unicode_literals

import logging
import time
import urllib

import pykka
from spotify import Link, SpotifyError

from mopidy.backends import base
from mopidy.models import Track, SearchResult

from . import translator

logger = logging.getLogger('mopidy.backends.spotify')

TRACK_AVAILABLE = 1


class SpotifyTrack(Track):
    """Proxy object for unloaded Spotify tracks."""
    def __init__(self, uri=None, track=None):
        super(SpotifyTrack, self).__init__()
        if (uri and track) or (not uri and not track):
            raise AttributeError('uri or track must be provided')
        elif uri:
            self._spotify_track = Link.from_string(uri).as_track()
        elif track:
            self._spotify_track = track
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
    def __init__(self, *args, **kwargs):
        super(SpotifyLibraryProvider, self).__init__(*args, **kwargs)
        self._timeout = self.backend.config['spotify']['timeout']

    def find_exact(self, query=None, uris=None):
        return self.search(query=query, uris=uris)

    def lookup(self, uri):
        try:
            link = Link.from_string(uri)
            if link.type() == Link.LINK_TRACK:
                return self._lookup_track(uri)
            if link.type() == Link.LINK_ALBUM:
                return self._lookup_album(uri)
            elif link.type() == Link.LINK_ARTIST:
                return self._lookup_artist(uri)
            elif link.type() == Link.LINK_PLAYLIST:
                return self._lookup_playlist(uri)
            else:
                return []
        except SpotifyError as error:
            logger.debug(u'Failed to lookup "%s": %s', uri, error)
            return []

    def _lookup_track(self, uri):
        track = Link.from_string(uri).as_track()
        self._wait_for_object_to_load(track)
        if track.is_loaded():
            if track.availability() == TRACK_AVAILABLE:
                return [SpotifyTrack(track=track)]
            else:
                return []
        else:
            return [SpotifyTrack(uri=uri)]

    def _lookup_album(self, uri):
        album = Link.from_string(uri).as_album()
        album_browser = self.backend.spotify.session.browse_album(album)
        self._wait_for_object_to_load(album_browser)
        return [
            SpotifyTrack(track=t)
            for t in album_browser if t.availability() == TRACK_AVAILABLE]

    def _lookup_artist(self, uri):
        artist = Link.from_string(uri).as_artist()
        artist_browser = self.backend.spotify.session.browse_artist(artist)
        self._wait_for_object_to_load(artist_browser)
        return [
            SpotifyTrack(track=t)
            for t in artist_browser if t.availability() == TRACK_AVAILABLE]

    def _lookup_playlist(self, uri):
        playlist = Link.from_string(uri).as_playlist()
        self._wait_for_object_to_load(playlist)
        return [
            SpotifyTrack(track=t)
            for t in playlist if t.availability() == TRACK_AVAILABLE]

    def _wait_for_object_to_load(self, spotify_obj, timeout=None):
        # XXX Sleeping to wait for the Spotify object to load is an ugly hack,
        # but it works. We should look into other solutions for this.
        if timeout is None:
            timeout = self._timeout
        wait_until = time.time() + timeout
        while not spotify_obj.is_loaded():
            time.sleep(0.1)
            if time.time() > wait_until:
                logger.debug(
                    'Timeout: Spotify object did not load in %ds', timeout)
                return

    def refresh(self, uri=None):
        pass  # TODO

    def search(self, query=None, uris=None):
        # TODO Only return results within URI roots given by ``uris``

        if not query:
            return self._get_all_tracks()

        uris = query.get('uri', [])
        if uris:
            tracks = []
            for uri in uris:
                tracks += self.lookup(uri)
            if len(uris) == 1:
                uri = uris[0]
            else:
                uri = 'spotify:search'
            return SearchResult(uri=uri, tracks=tracks)

        spotify_query = self._translate_search_query(query)
        logger.debug('Spotify search query: %s' % spotify_query)

        future = pykka.ThreadingFuture()

        def callback(results, userdata=None):
            search_result = SearchResult(
                uri='spotify:search:%s' % (
                    urllib.quote(results.query().encode('utf-8'))),
                albums=[
                    translator.to_mopidy_album(a) for a in results.albums()],
                artists=[
                    translator.to_mopidy_artist(a) for a in results.artists()],
                tracks=[
                    translator.to_mopidy_track(t) for t in results.tracks()])
            future.set(search_result)

        if not self.backend.spotify.connected.is_set():
            logger.debug('Not connected: Spotify search cancelled')
            return SearchResult(uri='spotify:search')

        self.backend.spotify.session.search(
            spotify_query, callback,
            album_count=200, artist_count=200, track_count=200)

        try:
            return future.get(timeout=self._timeout)
        except pykka.Timeout:
            logger.debug(
                'Timeout: Spotify search did not return in %ds', self._timeout)
            return SearchResult(uri='spotify:search')

    def _get_all_tracks(self):
        # Since we can't search for the entire Spotify library, we return
        # all tracks in the playlists when the query is empty.
        tracks = []
        for playlist in self.backend.playlists.playlists:
            tracks += playlist.tracks
        return SearchResult(uri='spotify:search', tracks=tracks)

    def _translate_search_query(self, mopidy_query):
        spotify_query = []
        for (field, values) in mopidy_query.iteritems():
            if field == 'date':
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
