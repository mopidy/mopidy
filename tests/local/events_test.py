from __future__ import unicode_literals

import unittest

import mock
import pykka

from mopidy import audio, backend, core
from mopidy.local import actor

from tests import path_to_data_dir


@mock.patch.object(backend.BackendListener, 'send')
class LocalBackendEventsTest(unittest.TestCase):
    config = {
        'local': {
            'media_dir': path_to_data_dir(''),
            'data_dir': path_to_data_dir(''),
            'playlists_dir': b'',
            'library': 'json',
        }
    }

    def setUp(self):
        self.audio = audio.DummyAudio.start().proxy()
        self.backend = actor.LocalBackend.start(
            config=self.config, audio=self.audio).proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()

    def tearDown(self):
        pykka.ActorRegistry.stop_all()

    def test_playlists_refresh_sends_playlists_loaded_event(self, send):
        send.reset_mock()
        self.core.playlists.refresh().get()
        self.assertEqual(send.call_args[0][0], 'playlists_loaded')
