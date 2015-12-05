from __future__ import absolute_import, unicode_literals

from mock import patch

from mopidy.mpd.protocol.status import SUBSYSTEMS

from tests.mpd import protocol


class IdleHandlerTest(protocol.BaseTestCase):

    def idle_event(self, subsystem):
        self.session.on_event(subsystem)

    def assertEqualEvents(self, events):  # noqa: N802
        self.assertEqual(set(events), self.context.events)

    def assertEqualSubscriptions(self, events):  # noqa: N802
        self.assertEqual(set(events), self.context.subscriptions)

    def assertNoEvents(self):  # noqa: N802
        self.assertEqualEvents([])

    def assertNoSubscriptions(self):  # noqa: N802
        self.assertEqualSubscriptions([])

    def test_base_state(self):
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle(self):
        self.send_request('idle')
        self.assertEqualSubscriptions(SUBSYSTEMS)
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_disables_timeout(self):
        self.send_request('idle')
        self.connection.disable_timeout.assert_called_once_with()

    def test_noidle(self):
        self.send_request('noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_player(self):
        self.send_request('idle player')
        self.assertEqualSubscriptions(['player'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_output(self):
        self.send_request('idle output')
        self.assertEqualSubscriptions(['output'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_player_playlist(self):
        self.send_request('idle player playlist')
        self.assertEqualSubscriptions(['player', 'playlist'])
        self.assertNoEvents()
        self.assertNoResponse()

    def test_idle_then_noidle(self):
        self.send_request('idle')
        self.send_request('noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('OK')

    def test_idle_then_noidle_enables_timeout(self):
        self.send_request('idle')
        self.send_request('noidle')
        self.connection.enable_timeout.assert_called_once_with()

    def test_idle_then_play(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.send_request('idle')
            self.send_request('play')
            stop_mock.assert_called_once_with()

    def test_idle_then_idle(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.send_request('idle')
            self.send_request('idle')
            stop_mock.assert_called_once_with()

    def test_idle_player_then_play(self):
        with patch.object(self.session, 'stop') as stop_mock:
            self.send_request('idle player')
            self.send_request('play')
            stop_mock.assert_called_once_with()

    def test_idle_then_player(self):
        self.send_request('idle')
        self.idle_event('player')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('OK')

    def test_idle_player_then_event_player(self):
        self.send_request('idle player')
        self.idle_event('player')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('OK')

    def test_idle_then_output(self):
        self.send_request('idle')
        self.idle_event('output')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('changed: output')
        self.assertOnceInResponse('OK')

    def test_idle_output_then_event_output(self):
        self.send_request('idle output')
        self.idle_event('output')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('changed: output')
        self.assertOnceInResponse('OK')

    def test_idle_player_then_noidle(self):
        self.send_request('idle player')
        self.send_request('noidle')
        self.assertNoSubscriptions()
        self.assertNoEvents()
        self.assertOnceInResponse('OK')

    def test_idle_player_playlist_then_noidle(self):
        self.send_request('idle player playlist')
        self.send_request('noidle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('OK')

    def test_idle_player_playlist_then_player(self):
        self.send_request('idle player playlist')
        self.idle_event('player')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertNotInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_idle_playlist_then_player(self):
        self.send_request('idle playlist')
        self.idle_event('player')
        self.assertEqualEvents(['player'])
        self.assertEqualSubscriptions(['playlist'])
        self.assertNoResponse()

    def test_idle_playlist_then_player_then_playlist(self):
        self.send_request('idle playlist')
        self.idle_event('player')
        self.idle_event('playlist')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertNotInResponse('changed: player')
        self.assertOnceInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_player(self):
        self.idle_event('player')
        self.assertEqualEvents(['player'])
        self.assertNoSubscriptions()
        self.assertNoResponse()

    def test_player_then_idle_player(self):
        self.idle_event('player')
        self.send_request('idle player')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertNotInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_player_then_playlist(self):
        self.idle_event('player')
        self.idle_event('playlist')
        self.assertEqualEvents(['player', 'playlist'])
        self.assertNoSubscriptions()
        self.assertNoResponse()

    def test_player_then_idle(self):
        self.idle_event('player')
        self.send_request('idle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('OK')

    def test_player_then_playlist_then_idle(self):
        self.idle_event('player')
        self.idle_event('playlist')
        self.send_request('idle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: player')
        self.assertOnceInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_player_then_idle_playlist(self):
        self.idle_event('player')
        self.send_request('idle playlist')
        self.assertEqualEvents(['player'])
        self.assertEqualSubscriptions(['playlist'])
        self.assertNoResponse()

    def test_player_then_idle_playlist_then_noidle(self):
        self.idle_event('player')
        self.send_request('idle playlist')
        self.send_request('noidle')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('OK')

    def test_player_then_playlist_then_idle_playlist(self):
        self.idle_event('player')
        self.idle_event('playlist')
        self.send_request('idle playlist')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertNotInResponse('changed: player')
        self.assertOnceInResponse('changed: playlist')
        self.assertOnceInResponse('OK')

    def test_output_then_idle_toggleoutput(self):
        self.idle_event('output')
        self.send_request('idle output')
        self.assertNoEvents()
        self.assertNoSubscriptions()
        self.assertOnceInResponse('changed: output')
        self.assertOnceInResponse('OK')
