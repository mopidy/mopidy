import logging
import Queue

from spotify import Link, SpotifyError

from mopidy.backends.base import BaseLibraryProvider
from mopidy.backends.spotify.translator import SpotifyTranslator
from mopidy.models import Playlist

logger = logging.getLogger('mopidy.backends.spotify.library')

class SpotifyLibraryProvider(BaseLibraryProvider):
    def find_exact(self, **query):
        return self.search(**query)

    def lookup(self, uri):
        try:
            spotify_track = Link.from_string(uri).as_track()
            # TODO Block until metadata_updated callback is called. Before that
            # the track will be unloaded, unless it's already in the stored
            # playlists.
            return SpotifyTranslator.to_mopidy_track(spotify_track)
        except SpotifyError as e:
            logger.debug(u'Failed to lookup "%s": %s', uri, e)
            return None

    def refresh(self, uri=None):
        pass # TODO

    def search(self, **query):
        if not query:
            # Since we can't search for the entire Spotify library, we return
            # all tracks in the stored playlists when the query is empty.
            tracks = []
            for playlist in self.backend.stored_playlists.playlists:
                tracks += playlist.tracks
            return Playlist(tracks=tracks)
        spotify_query = []
        for (field, values) in query.iteritems():
            if field == u'track':
                field = u'title'
            if field == u'date':
                field = u'year'
            if not hasattr(values, '__iter__'):
                values = [values]
            for value in values:
                if field == u'any':
                    spotify_query.append(value)
                elif field == u'year':
                    value = int(value.split('-')[0]) # Extract year
                    spotify_query.append(u'%s:%d' % (field, value))
                else:
                    spotify_query.append(u'%s:"%s"' % (field, value))
        spotify_query = u' '.join(spotify_query)
        logger.debug(u'Spotify search query: %s' % spotify_query)
        queue = Queue.Queue()
        self.backend.spotify.search(spotify_query, queue)
        try:
            return queue.get(timeout=3) # XXX What is an reasonable timeout?
        except Queue.Empty:
            return Playlist(tracks=[])
