import logging
import time

try:
    import pylast
except ImportError as import_error:
    from mopidy import OptionalDependencyError
    raise OptionalDependencyError(import_error)

from pykka.actor import ThreadingActor

from mopidy import settings, SettingsError
from mopidy.listeners import BackendListener

logger = logging.getLogger('mopidy.frontends.lastfm')

API_KEY = '2236babefa8ebb3d93ea467560d00d04'
API_SECRET = '94d9a09c0cd5be955c4afaeaffcaefcd'

class LastfmFrontend(ThreadingActor, BackendListener):
    """
    Frontend which scrobbles the music you play to your `Last.fm
    <http://www.last.fm>`_ profile.

    .. note::

        This frontend requires a free user account at Last.fm.

    **Dependencies:**

    - `pylast <http://code.google.com/p/pylast/>`_ >= 0.5.7

    **Settings:**

    - :attr:`mopidy.settings.LASTFM_USERNAME`
    - :attr:`mopidy.settings.LASTFM_PASSWORD`
    """

    def __init__(self):
        super(LastfmFrontend, self).__init__()
        self.lastfm = None
        self.last_start_time = None

    def on_start(self):
        try:
            username = settings.LASTFM_USERNAME
            password_hash = pylast.md5(settings.LASTFM_PASSWORD)
            self.lastfm = pylast.LastFMNetwork(
                api_key=API_KEY, api_secret=API_SECRET,
                username=username, password_hash=password_hash)
            logger.info(u'Connected to Last.fm')
        except SettingsError as e:
            logger.info(u'Last.fm scrobbler not started')
            logger.debug(u'Last.fm settings error: %s', e)
            self.stop()
        except (pylast.NetworkError, pylast.MalformedResponseError,
                pylast.WSError) as e:
            logger.error(u'Error during Last.fm setup: %s', e)
            self.stop()

    def track_playback_started(self, track):
        artists = ', '.join([a.name for a in track.artists])
        duration = track.length and track.length // 1000 or 0
        self.last_start_time = int(time.time())
        logger.debug(u'Now playing track: %s - %s', artists, track.name)
        try:
            self.lastfm.update_now_playing(
                artists,
                (track.name or ''),
                album=(track.album and track.album.name or ''),
                duration=str(duration),
                track_number=str(track.track_no),
                mbid=(track.musicbrainz_id or ''))
        except (pylast.ScrobblingError, pylast.NetworkError,
                pylast.MalformedResponseError, pylast.WSError) as e:
            logger.warning(u'Error submitting playing track to Last.fm: %s', e)

    def track_playback_ended(self, track, time_position):
        artists = ', '.join([a.name for a in track.artists])
        duration = track.length and track.length // 1000 or 0
        time_position = time_position // 1000
        if duration < 30:
            logger.debug(u'Track too short to scrobble. (30s)')
            return
        if time_position < duration // 2 and time_position < 240:
            logger.debug(
                u'Track not played long enough to scrobble. (50% or 240s)')
            return
        if self.last_start_time is None:
            self.last_start_time = int(time.time()) - duration
        logger.debug(u'Scrobbling track: %s - %s', artists, track.name)
        try:
            self.lastfm.scrobble(
                artists,
                (track.name or ''),
                str(self.last_start_time),
                album=(track.album and track.album.name or ''),
                track_number=str(track.track_no),
                duration=str(duration),
                mbid=(track.musicbrainz_id or ''))
        except (pylast.ScrobblingError, pylast.NetworkError,
                pylast.MalformedResponseError, pylast.WSError) as e:
            logger.warning(u'Error submitting played track to Last.fm: %s', e)
