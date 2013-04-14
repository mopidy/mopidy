from __future__ import unicode_literals

import logging
import time

import pykka
import pylast

from mopidy.core import CoreListener


logger = logging.getLogger('mopidy.frontends.scrobbler')

API_KEY = '2236babefa8ebb3d93ea467560d00d04'
API_SECRET = '94d9a09c0cd5be955c4afaeaffcaefcd'


class ScrobblerFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, config, core):
        super(ScrobblerFrontend, self).__init__()
        self.config = config
        self.lastfm = None
        self.last_start_time = None

    def on_start(self):
        try:
            self.lastfm = pylast.LastFMNetwork(
                api_key=API_KEY, api_secret=API_SECRET,
                username=self.config['scrobbler']['username'],
                password_hash=pylast.md5(self.config['scrobbler']['password']))
            logger.info('Scrobbler connected to Last.fm')
        except (pylast.NetworkError, pylast.MalformedResponseError,
                pylast.WSError) as e:
            logger.error('Error during Last.fm setup: %s', e)
            self.stop()

    def track_playback_started(self, tl_track):
        track = tl_track.track
        artists = ', '.join([a.name for a in track.artists])
        duration = track.length and track.length // 1000 or 0
        self.last_start_time = int(time.time())
        logger.debug('Now playing track: %s - %s', artists, track.name)
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
            logger.warning('Error submitting playing track to Last.fm: %s', e)

    def track_playback_ended(self, tl_track, time_position):
        track = tl_track.track
        artists = ', '.join([a.name for a in track.artists])
        duration = track.length and track.length // 1000 or 0
        time_position = time_position // 1000
        if duration < 30:
            logger.debug('Track too short to scrobble. (30s)')
            return
        if time_position < duration // 2 and time_position < 240:
            logger.debug(
                'Track not played long enough to scrobble. (50% or 240s)')
            return
        if self.last_start_time is None:
            self.last_start_time = int(time.time()) - duration
        logger.debug('Scrobbling track: %s - %s', artists, track.name)
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
            logger.warning('Error submitting played track to Last.fm: %s', e)
