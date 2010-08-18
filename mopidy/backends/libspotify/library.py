import logging
import multiprocessing

from spotify import Link

from mopidy.backends.base import BaseLibraryController
from mopidy.backends.libspotify import ENCODING
from mopidy.backends.libspotify.translator import LibspotifyTranslator

logger = logging.getLogger('mopidy.backends.libspotify.library')

class LibspotifyLibraryController(BaseLibraryController):
    def find_exact(self, **query):
        return self.search(**query)

    def lookup(self, uri):
        spotify_track = Link.from_string(uri).as_track()
        return LibspotifyTranslator.to_mopidy_track(spotify_track)

    def refresh(self, uri=None):
        pass # TODO

    def search(self, **query):
        spotify_query = []
        for (field, values) in query.iteritems():
            if not hasattr(values, '__iter__'):
                values = [values]
            for value in values:
                if field == u'track':
                    field = u'title'
                if field == u'any':
                    spotify_query.append(value)
                else:
                    spotify_query.append(u'%s:"%s"' % (field, value))
        spotify_query = u' '.join(spotify_query)
        logger.debug(u'Spotify search query: %s' % spotify_query)
        my_end, other_end = multiprocessing.Pipe()
        self.backend.spotify.search(spotify_query.encode(ENCODING), other_end)
        my_end.poll(None)
        playlist = my_end.recv()
        return playlist
