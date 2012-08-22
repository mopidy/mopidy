import logging

from spotify.manager import SpotifyContainerManager as \
    PyspotifyContainerManager

logger = logging.getLogger('mopidy.backends.spotify.container_manager')

class SpotifyContainerManager(PyspotifyContainerManager):
    def __init__(self, session_manager):
        PyspotifyContainerManager.__init__(self)
        self.session_manager = session_manager

    def container_loaded(self, container, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: playlist container loaded')

        self.session_manager.refresh_stored_playlists()

        count = 0
        for playlist in self.session_manager.session.playlist_container():
            if playlist.type() == 'playlist':
                self.session_manager.playlist_manager.watch(playlist)
                count += 1
        logger.debug(u'Watching %d playlist(s) for changes', count)

    def playlist_added(self, container, playlist, position, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: playlist added at position %d',
            position)
        # container_loaded() is called after this callback, so we do not need
        # to handle this callback.

    def playlist_moved(self, container, playlist, old_position, new_position,
            userdata):
        """Callback used by pyspotify"""
        logger.debug(
            u'Callback called: playlist "%s" moved from position %d to %d',
            playlist.name(), old_position, new_position)
        # container_loaded() is called after this callback, so we do not need
        # to handle this callback.

    def playlist_removed(self, container, playlist, position, userdata):
        """Callback used by pyspotify"""
        logger.debug(
            u'Callback called: playlist "%s" removed from position %d',
            playlist.name(), position)
        # container_loaded() is called after this callback, so we do not need
        # to handle this callback.
