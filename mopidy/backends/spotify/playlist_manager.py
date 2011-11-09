import datetime
import logging

from spotify.manager import SpotifyPlaylistManager as PyspotifyPlaylistManager

logger = logging.getLogger('mopidy.backends.spotify.playlist_manager')

class SpotifyPlaylistManager(PyspotifyPlaylistManager):
    def __init__(self, session_manager):
        PyspotifyPlaylistManager.__init__(self)
        self.session_manager = session_manager

    def tracks_added(self, playlist, tracks, position, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: '
            u'%d track(s) added to position %d in playlist "%s"',
            len(tracks), position, playlist.name())
        self.session_manager.refresh_stored_playlists()

    def tracks_moved(self, playlist, tracks, new_position, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: '
            u'%d track(s) moved to position %d in playlist "%s"',
            len(tracks), new_position, playlist.name())
        self.session_manager.refresh_stored_playlists()

    def tracks_removed(self, playlist, tracks, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: '
            u'%d track(s) removed from playlist "%s"',
            len(tracks), playlist.name())
        self.session_manager.refresh_stored_playlists()

    def playlist_renamed(self, playlist, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: Playlist renamed to "%s"',
            playlist.name())
        self.session_manager.refresh_stored_playlists()

    def playlist_state_changed(self, playlist, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: The state of playlist "%s" changed',
            playlist.name())

    def playlist_update_in_progress(self, playlist, done, userdata):
        """Callback used by pyspotify"""
        if done:
            logger.debug(u'Callback called: '
                u'Update of playlist "%s" done', playlist.name())
        else:
            logger.debug(u'Callback called: '
                u'Update of playlist "%s" in progress', playlist.name())

    def playlist_metadata_updated(self, playlist, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: Metadata updated for playlist "%s"',
            playlist.name())

    def track_created_changed(self, playlist, position, user, when, userdata):
        """Callback used by pyspotify"""
        when = datetime.datetime.fromtimestamp(when)
        logger.debug(
            u'Callback called: Created by/when for track %d in playlist '
            u'"%s" changed to user "N/A" and time "%s"',
            position, playlist.name(), when)

    def track_message_changed(self, playlist, position, message, userdata):
        """Callback used by pyspotify"""
        logger.debug(
            u'Callback called: Message for track %d in playlist '
            u'"%s" changed to "%s"', position, playlist.name(), message)

    def track_seen_changed(self, playlist, position, seen, userdata):
        """Callback used by pyspotify"""
        logger.debug(
            u'Callback called: Seen attribute for track %d in playlist '
            u'"%s" changed to "%s"', position, playlist.name(), seen)

    def description_changed(self, playlist, description, userdata):
        """Callback used by pyspotify"""
        logger.debug(
            u'Callback called: Description changed for playlist "%s" to "%s"',
            playlist.name(), description)

    def subscribers_changed(self, playlist, userdata):
        """Callback used by pyspotify"""
        logger.debug(
            u'Callback called: Subscribers changed for playlist "%s"',
            playlist.name())

    def image_changed(self, playlist, image, userdata):
        """Callback used by pyspotify"""
        logger.debug(u'Callback called: Image changed for playlist "%s"',
            playlist.name())
