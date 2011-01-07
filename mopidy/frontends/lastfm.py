import logging
import multiprocessing
import socket
import time

try:
    import pylast
except ImportError as import_error:
    from mopidy import OptionalDependencyError
    raise OptionalDependencyError(import_error)

from mopidy import get_version, settings, SettingsError
from mopidy.frontends.base import BaseFrontend
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.frontends.lastfm')

CLIENT_ID = u'mop'
CLIENT_VERSION = get_version()

# pylast raises UnicodeEncodeError on conversion from unicode objects to
# ascii-encoded bytestrings, so we explicitly encode as utf-8 before passing
# strings to pylast.
ENCODING = u'utf-8'

class LastfmFrontend(BaseFrontend):
    """
    Frontend which scrobbles the music you play to your `Last.fm
    <http://www.last.fm>`_ profile.

    .. note::

        This frontend requires a free user account at Last.fm.

    **Dependencies:**

    - `pylast <http://code.google.com/p/pylast/>`_ >= 0.4.30

    **Settings:**

    - :attr:`mopidy.settings.LASTFM_USERNAME`
    - :attr:`mopidy.settings.LASTFM_PASSWORD`
    """

    def __init__(self, *args, **kwargs):
        super(LastfmFrontend, self).__init__(*args, **kwargs)
        (self.connection, other_end) = multiprocessing.Pipe()
        self.thread = LastfmFrontendThread(self.core_queue, other_end)

    def start(self):
        self.thread.start()

    def destroy(self):
        self.thread.destroy()

    def process_message(self, message):
        if self.thread.is_alive():
            self.connection.send(message)


class LastfmFrontendThread(BaseThread):
    def __init__(self, core_queue, connection):
        super(LastfmFrontendThread, self).__init__(core_queue)
        self.name = u'LastfmFrontendThread'
        self.connection = connection
        self.lastfm = None
        self.scrobbler = None
        self.last_start_time = None

    def run_inside_try(self):
        self.setup()
        while self.scrobbler is not None:
            self.connection.poll(None)
            message = self.connection.recv()
            self.process_message(message)

    def setup(self):
        try:
            username = settings.LASTFM_USERNAME
            password_hash = pylast.md5(settings.LASTFM_PASSWORD)
            self.lastfm = pylast.get_lastfm_network(
                username=username, password_hash=password_hash)
            self.scrobbler = self.lastfm.get_scrobbler(
                CLIENT_ID, CLIENT_VERSION)
            logger.info(u'Connected to Last.fm')
        except SettingsError as e:
            logger.info(u'Last.fm scrobbler not started')
            logger.debug(u'Last.fm settings error: %s', e)
        except (pylast.WSError, socket.error) as e:
            logger.error(u'Last.fm connection error: %s', e)

    def process_message(self, message):
        if message['command'] == 'started_playing':
            self.started_playing(message['track'])
        elif message['command'] == 'stopped_playing':
            self.stopped_playing(message['track'], message['stop_position'])
        else:
            pass # Ignore commands for other frontends

    def started_playing(self, track):
        artists = ', '.join([a.name for a in track.artists])
        duration = track.length // 1000
        self.last_start_time = int(time.time())
        logger.debug(u'Now playing track: %s - %s', artists, track.name)
        try:
            self.scrobbler.report_now_playing(
                artists.encode(ENCODING),
                track.name.encode(ENCODING),
                album=track.album.name.encode(ENCODING),
                duration=duration,
                track_number=track.track_no)
        except (pylast.ScrobblingError, socket.error) as e:
            logger.warning(u'Last.fm now playing error: %s', e)

    def stopped_playing(self, track, stop_position):
        artists = ', '.join([a.name for a in track.artists])
        duration = track.length // 1000
        stop_position = stop_position // 1000
        if duration < 30:
            logger.debug(u'Track too short to scrobble. (30s)')
            return
        if stop_position < duration // 2 and stop_position < 240:
            logger.debug(
                u'Track not played long enough to scrobble. (50% or 240s)')
            return
        if self.last_start_time is None:
            self.last_start_time = int(time.time()) - duration
        logger.debug(u'Scrobbling track: %s - %s', artists, track.name)
        try:
            self.scrobbler.scrobble(
                artists.encode(ENCODING),
                track.name.encode(ENCODING),
                time_started=self.last_start_time,
                source=pylast.SCROBBLE_SOURCE_USER,
                mode=pylast.SCROBBLE_MODE_PLAYED,
                duration=duration,
                album=track.album.name.encode(ENCODING),
                track_number=track.track_no)
        except (pylast.ScrobblingError, socket.error) as e:
            logger.warning(u'Last.fm scrobbling error: %s', e)
