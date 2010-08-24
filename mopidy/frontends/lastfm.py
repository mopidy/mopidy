import logging
import multiprocessing
import socket
import time

import pylast

from mopidy import get_version, settings, SettingsError
from mopidy.frontends.base import BaseFrontend
from mopidy.utils.process import BaseProcess

logger = logging.getLogger('mopidy.frontends.lastfm')

CLIENT_ID = u'mop'
CLIENT_VERSION = get_version()

# pylast raises UnicodeEncodeError on conversion from unicode objects to
# ascii-encoded bytestrings, so we explicitly encode as utf-8 before passing
# strings to pylast.
ENCODING = u'utf-8'

class LastfmFrontend(BaseFrontend):
    """
    Frontend which scrobbles the music you plays to your Last.fm profile.

    **Dependencies:**

    - `pylast <http://code.google.com/p/pylast/>`_ >= 0.4.30

    **Settings:**

    - :mod:`mopidy.settings.LASTFM_USERNAME`
    - :mod:`mopidy.settings.LASTFM_PASSWORD`
    """

    # TODO Add docs
    # TODO Log nice error message if pylast isn't found

    def __init__(self, *args, **kwargs):
        super(LastfmFrontend, self).__init__(*args, **kwargs)
        (self.connection, other_end) = multiprocessing.Pipe()
        self.process = LastfmFrontendProcess(other_end)

    def start(self):
        self.process.start()

    def destroy(self):
        self.process.destroy()

    def process_message(self, message):
        self.connection.send(message)


class LastfmFrontendProcess(BaseProcess):
    def __init__(self, connection):
        super(LastfmFrontendProcess, self).__init__()
        self.name = u'LastfmFrontendProcess'
        self.daemon = True
        self.connection = connection
        self.lastfm = None
        self.scrobbler = None

    def run_inside_try(self):
        self.setup()
        while True:
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
            logger.info(u'Last.fm scrobbler did not start.')
            logger.debug(u'Last.fm settings error: %s', e)
        except (pylast.WSError, socket.error) as e:
            logger.error(u'Last.fm connection error: %s', e)

    def process_message(self, message):
        if message['command'] == 'now_playing':
            self.report_now_playing(message['track'])
        elif message['command'] == 'end_of_track':
            self.scrobble(message['track'])
        else:
            pass # Ignore commands for other frontends

    def report_now_playing(self, track):
        artists = ', '.join([a.name for a in track.artists])
        logger.debug(u'Now playing track: %s - %s', artists, track.name)
        duration = track.length // 1000
        try:
            self.scrobbler.report_now_playing(
                artists.encode(ENCODING),
                track.name.encode(ENCODING),
                album=track.album.name.encode(ENCODING),
                duration=duration,
                track_number=track.track_no)
        except (pylast.ScrobblingError, socket.error) as e:
            logger.error(u'Last.fm now playing error: %s', e)

    def scrobble(self, track):
        artists = ', '.join([a.name for a in track.artists])
        logger.debug(u'Scrobbling track: %s - %s', artists, track.name)
        # TODO Scrobble if >50% or >240s of a track has been played
        # TODO Do not scrobble if duration <30s
        # FIXME Get actual time when track started playing
        duration = track.length // 1000
        time_started = int(time.time()) - duration
        try:
            self.scrobbler.scrobble(
                artists.encode(ENCODING),
                track.name.encode(ENCODING),
                time_started=time_started,
                source=pylast.SCROBBLE_SOURCE_USER,
                mode=pylast.SCROBBLE_MODE_PLAYED,
                duration=duration,
                album=track.album.name.encode(ENCODING),
                track_number=track.track_no)
        except (pylast.ScrobblingError, socket.error) as e:
            logger.error(u'Last.fm scrobbling error: %s', e)
