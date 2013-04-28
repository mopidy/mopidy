from __future__ import unicode_literals

import mock
import pykka

from mopidy import core, audio
from mopidy.backends import listener


@mock.patch.object(listener.BackendListener, 'send')
class BackendEventsTest(object):
    config = {}

    def setUp(self):
        self.audio = audio.DummyAudio.start().proxy()
        self.backend = self.backend_class.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_playlists_refresh_sends_playlists_loaded_event(self, send):
        send.reset_mock()
        self.core.playlists.refresh().get()
        self.assertEqual(send.call_args[0][0], 'playlists_loaded')
