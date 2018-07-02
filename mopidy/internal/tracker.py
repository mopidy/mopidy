from __future__ import absolute_import, unicode_literals

import logging
import os
import sqlite3
from threading import Timer

import pykka

from mopidy.internal import path

logger = logging.getLogger(__name__)


class PlaybackTracker(object):
    positions = {}

    def __init__(self, playback_controller, config, *args, **kwargs):
        self.playback_controller = playback_controller
        self.config = config

        self.enabled = True
        self._timer = None
        self.interval = 5  # save position every x seconds
        self.is_running = False
        try:
            self.db_path = os.path.join(self._get_data_dir(),
                                        b'playback_positions.db')
        except (KeyError, TypeError):
            self.enabled = False

        # Get enabled types from core config
        try:
            enabled_types = self.config['core']['continue_playback_types']
            self.types = tuple(enabled_types.split(','))
        except (KeyError, TypeError):
            self.types = ()
            self.enabled = False

        if self.enabled:
            self.start()

    def _setup_db(self):
        return self._execute_db_query('''
            CREATE TABLE playback_position
            (id integer primary key autoincrement,
            uri text not null unique,
            position int)
            ''')

    def _execute_db_query(self, *args):
        con = sqlite3.connect(self.db_path)
        c = con.cursor()
        try:
            result = c.execute(*args).fetchone()
        except sqlite3.OperationalError:
            # If the db isn't set up yet, do this first, then try again
            self._setup_db()
            result = c.execute(*args).fetchone()
        con.commit()
        con.close()

        return result

    def _run(self):
        self.is_running = False
        self.start()
        self.save_position()

    # Start the tracker, i.e. periodically saving the playback position
    def start(self):
        if self.enabled and not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    # Stop the tracker
    def stop(self):
        if self._timer:
            self._timer.cancel()
        self.is_running = False

    # Save the current playback position in ms to a Sqlite3 DB
    def save_position(self):
        if not self.enabled:
            return False

        track = self.playback_controller.get_current_track()
        try:
            time_position = self.playback_controller.get_time_position()
        except pykka.ActorDeadError:
            return False
        if track and isinstance(time_position, (int, long)):
            self._execute_db_query('''
                                   INSERT OR REPLACE INTO playback_position
                                   (uri, position) VALUES (?, ?)''',
                                   (track.uri, time_position))
            logger.debug("Saving playback position for %s at %dms"
                         % (track.name, time_position))
            return True

    # Try to retrieve a previous playback positoin from the DB
    def get_last_position(self, track_uri):
        if not self.enabled:
            return None

        try:
            result = self._execute_db_query('''
                SELECT position FROM playback_position
                WHERE uri = ?''', (track_uri,))
            position = result[0]
        except TypeError:
            position = None
        return position

    # Check if the file's "type" is enabled to be able to be continued
    # We do this by checking the track's uri's prefix to be checked
    # against a list given in the config
    def is_track_enabled_for_tracking(self, track):
        return track.uri.startswith(self.types)

    # TODO: refactor this as it's a duplicate of core.actor._get_data_dir
    def _get_data_dir(self):
        data_dir_path = os.path.join(self.config['core']['data_dir'], b'core')
        path.get_or_create_dir(data_dir_path)
        return data_dir_path
