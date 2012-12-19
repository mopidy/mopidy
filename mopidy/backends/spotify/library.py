from __future__ import unicode_literals

import logging
import Queue
import time

from spotify import Link, SpotifyError

from mopidy.backends import base
from mopidy.models import Track

from . import translator

logger = logging.getLogger('mopidy.backends.spotify')


class SpotifyTrack(Track):
    """Proxy object for unloaded Spotify tracks."""
    def __init__(self, uri=None, track=None):
        super(SpotifyTrack, self).__init__()
        if uri:
            self._spotify_track = Link.from_string(uri).as_track()
        elif track:
            self._spotify_track = track
        else:
            raise AttributeError('uri or track must be provided')
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
        return [SpotifyTrack(uri)]

    def _lookup_album(self, uri):
        album = Link.from_string(uri).as_album()
        album_browser = self.backend.spotify.session.browse_album(album)
        self._wait_for_object_to_load(album_browser)
        return [SpotifyTrack(track=t) for t in album_browser]

    def _lookup_artist(self, uri):
        artist = Link.from_string(uri).as_artist()
        artist_browser = self.backend.spotify.session.browse_artist(artist)
        self._wait_for_object_to_load(artist_browser)
        return [SpotifyTrack(track=t) for t in artist_browser]

    def _lookup_playlist(self, uri):
        playlist = Link.from_string(uri).as_playlist()
        self._wait_for_object_to_load(playlist)
        return [SpotifyTrack(track=t) for t in playlist]

    def _wait_for_object_to_load(self, spotify_obj, timeout=10):
        # XXX Sleeping to wait for the Spotify object to load is an ugly hack,
        # but it works. We should look into other solutions for this.
        start = time.time()
        while not spotify_obj.is_loaded():
            time.sleep(0.1)
            if time.time() > (start + timeout):
                logger.debug(
                    'Timeout: Spotify object did not load in %ds', timeout)
                return

    def refresh(self, uri=None):
        pass  # TODO

    def search(self, **query):
        if not query:
            # Since we can't search for the entire Spotify library, we return
            # all tracks in the playlists when the query is empty.
            tracks = []
            for playlist in self.backend.playlists.playlists:
                tracks += playlist.tracks
            return tracks
        spotify_query = []
        for (field, values) in query.iteritems():
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
        logger.debug('Spotify search query: %s' % spotify_query)
        queue = Queue.Queue()
        self.backend.spotify.search(spotify_query, queue)
        try:
            return queue.get(timeout=3)  # XXX What is an reasonable timeout?
        except Queue.Empty:
            return []
