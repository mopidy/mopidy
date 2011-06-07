import logging

from spotify.manager import SpotifyContainerManager as PyspotifyContainerManager

logger = logging.getLogger('mopidy.backends.spotify.container_manager')

class SpotifyContainerManager(PyspotifyContainerManager):

    def __init__(self, session_manager):
        PyspotifyContainerManager.__init__(self)
        self.session_manager = session_manager

    def container_loaded(self, container, userdata):
        """Callback used by pyspotify."""
        logger.debug(u'Container loaded')
        self.session_manager.refresh_stored_playlists()
