import logging
import multiprocessing

from spotify import Link, SpotifyError

from mopidy.backends.base import BaseLibraryProvider
from mopidy.backends.libspotify import ENCODING
from mopidy.backends.libspotify.translator import LibspotifyTranslator
from mopidy.models import Playlist

logger = logging.getLogger('mopidy.backends.libspotify.library')

class LibspotifyLibraryProvider(BaseLibraryProvider):
    def find_exact(self, **query):
        return self.search(**query)

    def lookup(self, uri):
        try:
            spotify_track = Link.from_string(uri).as_track()
            # TODO Block until metadata_updated callback is called. Before that
            # the track will be unloaded, unless it's already in the stored
            # playlists.
            return LibspotifyTranslator.to_mopidy_track(spotify_track)
        except SpotifyError as e:
            logger.warning(u'Failed to lookup: %s', uri, e)
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
        my_end, other_end = multiprocessing.Pipe()
        self.backend.spotify.search(spotify_query.encode(ENCODING), other_end)
        my_end.poll(None)
        playlist = my_end.recv()
        return playlist
