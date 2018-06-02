from __future__ import absolute_import, unicode_literals

from threading import Timer

import logging

logger = logging.getLogger(__name__)


class PlaybackTracker(object):
    positions = {}

    def __init__(self, playback_controller, *args, **kwargs):
        self._timer = None
        self.interval = 5  # save position every x seconds
        self.playback_controller = playback_controller
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.save_position()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def save_position(self):
        track = self.playback_controller.get_current_track()
        time_position = self.playback_controller.get_time_position()
        if track and isinstance(time_position, (int, long)):
            self.positions[track.uri] = time_position
            logger.debug("Saving playback position for %s at %dms"
                         % (track.name, time_position))

    def get_last_position(self, track_uri):
        try:
            return self.positions[track_uri]
        except KeyError:
            return None
