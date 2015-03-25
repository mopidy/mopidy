from __future__ import absolute_import, unicode_literals

import datetime
import logging

import time

import unittest

import gobject

import mock

gobject.threads_init()

from mopidy import backend, core
from mopidy.audio import PlaybackState
from mopidy.models import Track

logger = logging.getLogger(__name__)


class SleeptimerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.playback1 = mock.Mock(spec=backend.PlaybackProvider)
        self.playback1.get_time_position().get.return_value = 1000
        self.playback1.reset_mock()
        self.backend1.playback = self.playback1

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.playback2 = mock.Mock(spec=backend.PlaybackProvider)
        self.playback2.get_time_position().get.return_value = 2000
        self.playback2.reset_mock()
        self.backend2.playback = self.playback2

        # A backend without the optional playback provider
        self.backend3 = mock.Mock()
        self.backend3.uri_schemes.get.return_value = ['dummy3']
        self.backend3.has_playback().get.return_value = False

        self.tracks = [
            Track(uri='dummy1:a', length=40000),
            Track(uri='dummy2:a', length=40000),
            Track(uri='dummy3:a', length=40000),  # Unplayable
            Track(uri='dummy1:b', length=40000),
        ]

        self.core = core.Core(mixer=None, backends=[
            self.backend1, self.backend2, self.backend3])
        self.core.tracklist.add(self.tracks)

        self.tl_tracks = self.core.tracklist.tl_tracks
        self.unplayable_tl_track = self.tl_tracks[2]

    def teardown(self):
        # make sure we don't leave it running
        self.core.sleeptimer.cancel()

    def test_start_updates_state(self):
        self.core.sleeptimer.start(1)
        st_state = self.core.sleeptimer.get_state()
        self.assertTrue(st_state['running'])
        self.core.sleeptimer.cancel()

    def test_cancel_updates_state(self):
        self.core.sleeptimer.start(1)
        st_state = self.core.sleeptimer.get_state()
        self.assertTrue(st_state['running'])

        self.core.sleeptimer.cancel()
        st_state = self.core.sleeptimer.get_state()
        self.assertFalse(st_state['running'])

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_start_emits_events(self, listener_mock):
        self.core.sleeptimer.cancel()

        listener_mock.reset_mock()

        self.core.sleeptimer.start(1, False)

        self.assertTrue(len(listener_mock.send.mock_calls) > 0)

        # TODO: is there a better way to test partial tuples
        # # ie where you only care about some of the values?
        mock_call = listener_mock.send.mock_calls[0]
        method, event_name, params = mock_call
        was_running = params['was_running']
        duration = params['duration']

        self.assertTrue(event_name[0] == 'sleeptimer_started')
        self.assertTrue(duration == 1)
        self.assertTrue(was_running is False)

        self.core.sleeptimer.cancel()

    @mock.patch(
        'mopidy.core.playback.listener.CoreListener', spec=core.CoreListener)
    def test_timer_expiring_stops_playback(self, listener_mock):
        self.core.playback.play(self.tl_tracks[0])
        pb_state = self.core.playback.get_state()
        self.assertTrue(pb_state == PlaybackState.PLAYING)
        listener_mock.reset_mock()

        loop = gobject.MainLoop()
        context = loop.get_context()

        check1_time = datetime.datetime.now() + datetime.timedelta(seconds=0.8)
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=1.2)

        self.core.sleeptimer.start(1)

        # check that it doesn't stop early
        while datetime.datetime.now() < check1_time:
            context.iteration(False)
            time.sleep(0.1)

        pb_state = self.core.playback.get_state()
        self.assertTrue(pb_state == PlaybackState.PLAYING)

        # check that it stopped
        while datetime.datetime.now() < end_time:
            context.iteration(False)
            time.sleep(0.2)

        pb_state = self.core.playback.get_state()
        self.assertTrue(pb_state == PlaybackState.STOPPED)

        # check that the right events were fired
        self.assertTrue(len(listener_mock.send.mock_calls) > 0)

        got_start_event = False
        got_tick_event = False
        got_end_event = False

        for idx in range(len(listener_mock.send.mock_calls)):

            mock_call = listener_mock.send.mock_calls[idx]
            method, event_name, params = mock_call

            if event_name[0] == 'sleeptimer_started':
                got_start_event = True
            if event_name[0] == 'sleeptimer_tick':
                got_tick_event = True
            if event_name[0] == 'sleeptimer_expired':
                got_end_event = True

        self.assertTrue(got_start_event)
        self.assertTrue(got_tick_event)
        self.assertTrue(got_end_event)
