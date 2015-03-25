from __future__ import absolute_import, unicode_literals

import datetime
import logging

import threading

import gobject

from mopidy.audio import PlaybackState
from mopidy.core import listener


logger = logging.getLogger(__name__)


class SleepTimerController(object):
    pykka_traversable = True

    def __init__(self, playback, core):
        logger.debug('Core.SleepTimer __init__')
        self.playback = playback
        self.core = core

        self._cancelevent = threading.Event()
        self._state = SleeptimerState()
        self._state.__init__()
        self._timer_id = None

    def get_state(self):
        return {"running": self._state.running,
                "duration": self._state.duration,
                "seconds_left": self._get_seconds_left()}

    def _get_seconds_left(self):
        seconds_left = 0

        if self._state.running:
            now = datetime.datetime.now()
            time_left = self._state.timerEndTime - now
            seconds_left = time_left.total_seconds()

            if seconds_left < 0:
                seconds_left = 0

        return seconds_left

    def cancel(self, notify=True):
        logger.debug('Cancel')

        self._cancelevent.set()
        self._state.clear()

        if notify:
            listener.CoreListener.send(
                'sleeptimer_cancelled')

    def start(self, duration, send_tick_events=True):
        old_state = self._state.running
        logger.debug('Start - state = %s, duration = %d', old_state, duration)

        if self._state.running:
            self.cancel(False)

        self._state.start(duration)

        self._cancelevent.clear()

        gobject.timeout_add(500, self._tick_handler)

        listener.CoreListener.send(
            'sleeptimer_started',
            was_running=old_state,
            duration=self._state.duration,
            seconds_left=self._get_seconds_left())

    def _tick_handler(self):
        if self._cancelevent.is_set():
            logger.debug('tick_handler, cancelevent is set')
            return False

        logger.debug('time left = %s',
                     self._get_seconds_left())

        if datetime.datetime.now() > self._state.timerEndTime:
            self._cancelevent.set()

            logger.debug('stopping, current playback state = %s',
                         self.playback.get_state())

            if self.playback.get_state() != PlaybackState.STOPPED:
                self.playback.stop()

            logger.debug('stopped, current playback state = %s',
                         self.playback.get_state())

            listener.CoreListener.send(
                'sleeptimer_expired')

            self._state.clear()

            return False
        else:
            if self._state.send_tick_events:
                listener.CoreListener.send(
                    'sleeptimer_tick',
                    seconds_left=self._get_seconds_left())

            return True


class SleeptimerState(object):
    pykka_traversable = True

    def __init__(self):
        self.running = False
        self.timerStartTime = None
        self.timerEndTime = None
        self.duration = 0
        self.send_tick_events = True

    def clear(self):
        self.running = False
        self.timerStartTime = None
        self.timerEndTime = None
        self.duration = 0
        self.send_tick_events = True

    def start(self, duration, send_tick_events=True):
        self.running = True
        self.timerStartTime = datetime.datetime.now()
        self.timerEndTime = \
            self.timerStartTime + datetime.timedelta(seconds=duration)
        self.duration = duration
        self.send_tick_events = send_tick_events

        logger.debug('SleepTimerState.start: running = %s, end time = %s',
                     self.running, self.timerEndTime)
