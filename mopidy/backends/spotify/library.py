import logging
import Queue
import time
from spotify import Link, SpotifyError #, Albumbrowser, Artistbrowser, ToplistBrowser

from mopidy.backends.base import BaseLibraryProvider
from mopidy.backends.spotify.translator import SpotifyTranslator
from mopidy.models import Playlist

TIME_OUT = 10

logger = logging.getLogger('mopidy.backends.spotify.library')

class SpotifyLibraryProvider(BaseLibraryProvider):
    def find_exact(self, **query):
        return self.search(**query)

    def lookup(self, uri):
        link = Link.from_string(uri)
        #uri is an album
        if link.type() == Link.LINK_ALBUM:
            try:
                logger.info('album')
                spotify_album = Link.from_string(uri).as_album()
                # TODO Block until metadata_updated callback is called. Before that
                # the track will be unloaded, unless it's already in the stored
                # playlists.
                browser = self.backend.spotify.session.browse_album(spotify_album)
                #wait 5 seconds
                start = time.time()
                while not browser.is_loaded():
                    time.sleep(0.1)
                    if time.time() > (start + TIME_OUT):
                        break
                album = SpotifyTranslator.to_mopidy_album(spotify_album)
                logger.info(browser)
                #for track in browser:
                #    track = SpotifyTranslator.to_mopidy_track(track)
                
                #from translator
                tracks=[SpotifyTranslator.to_mopidy_track(t) for t in browser
                    if str(Link.from_track(t, 0))]
                
                playlist = Playlist(tracks=tracks, uri=uri, name=album.name)
                return playlist
            
            except SpotifyError as e:
                logger.debug(u'Failed to lookup album "%s": %s', uri, e)
                return None
        
        #uri is an album
        if link.type() == Link.LINK_ARTIST:
            try:
                logger.info('artist')
                spotify_artist = Link.from_string(uri).as_artist()
                # TODO Block until metadata_updated callback is called. Before that
                # the track will be unloaded, unless it's already in the stored
                # playlists.
                browser = self.backend.spotify.session.browse_artist(spotify_artist)
                #wait 5 seconds
                start = time.time()
                while not browser.is_loaded():
                    time.sleep(0.1)
                    if time.time() > (start + TIME_OUT):
                        break
                artist = SpotifyTranslator.to_mopidy_artist(spotify_artist)
                logger.info(browser)
                #for track in browser:
                #    track = SpotifyTranslator.to_mopidy_track(track)
                
                #from translator
                tracks=[SpotifyTranslator.to_mopidy_track(t) for t in browser
                    if str(Link.from_track(t, 0))]
                
                playlist = Playlist(tracks=tracks, uri=uri, name=artist.name)
                return playlist
            
            except SpotifyError as e:
                logger.debug(u'Failed to lookup album "%s": %s', uri, e)
                return None
        
        #uri is a playlist of another user
#                if l.type() == Link.LINK_PLAYLIST:
#                if l.type() == Link.LINK_USER:
        
        #uri is a track
        try:
            logger.info('track')
            spotify_track = Link.from_string(uri).as_track()
            # TODO Block until metadata_updated callback is called. Before that
            # the track will be unloaded, unless it's already in the stored
            # playlists.
            return SpotifyTranslator.to_mopidy_track(spotify_track)
        except SpotifyError as e:
            logger.debug(u'Failed to lookup track "%s": %s', uri, e)
            return None

    def refresh(self, uri=None):
        pass # TODO

    def search(self, **query):
        uri = "spotify:search:"
        if not query:
            # Since we can't search for the entire Spotify library, we return
            # all tracks in the stored playlists when the query is empty.
            tracks = []
            for playlist in self.backend.stored_playlists.playlists:
                tracks += playlist.tracks
            return Playlist(tracks=tracks, uri=uri)
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
        uri = uri + spotify_query
        logger.debug(u'Spotify search query: %s' % spotify_query)
        queue = Queue.Queue()
        self.backend.spotify.search(spotify_query, queue)
        try:
            pl = queue.get(timeout=TIME_OUT) # XXX What is an reasonable timeout?
            return Playlist(tracks = pl.tracks, uri = uri)
        except Queue.Empty:
            return Playlist(tracks=[], uri=uri)
