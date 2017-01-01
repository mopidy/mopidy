from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
import unittest

import mock

import pykka

import mopidy

from mopidy.core import Core
from mopidy.internal import models, storage, versioning
from mopidy.models import Track
from tests import dummy_mixer


class CoreActorTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.backend1 = mock.Mock()
        self.backend1.uri_schemes.get.return_value = ['dummy1']
        self.backend1.actor_ref.actor_class.__name__ = b'B1'

        self.backend2 = mock.Mock()
        self.backend2.uri_schemes.get.return_value = ['dummy2']
        self.backend2.actor_ref.actor_class.__name__ = b'B2'

        self.core = Core(mixer=None, backends=[self.backend1, self.backend2])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def test_uri_schemes_has_uris_from_all_backends(self):
        result = self.core.uri_schemes

        self.assertIn('dummy1', result)
        self.assertIn('dummy2', result)

    def test_backends_with_colliding_uri_schemes_fails(self):
        self.backend2.uri_schemes.get.return_value = ['dummy1', 'dummy2']

        self.assertRaisesRegexp(
            AssertionError,
            'Cannot add URI scheme "dummy1" for B2, '
            'it is already handled by B1',
            Core, mixer=None, backends=[self.backend1, self.backend2])

    def test_version(self):
        self.assertEqual(self.core.version, versioning.get_version())


class CoreActorSaveLoadStateTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir,
                                       b'core', b'state.json.gz')

        config = {
            'core': {
                'max_tracklist_length': 10000,
                'restore_state': True,
                'data_dir': self.temp_dir,
            }
        }

        os.mkdir(os.path.join(self.temp_dir, b'core'))

        self.mixer = dummy_mixer.create_proxy()
        self.core = Core(
            config=config, mixer=self.mixer, backends=[])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()
        shutil.rmtree(self.temp_dir)

    def test_save_state(self):
        self.core.teardown()

        assert os.path.isfile(self.state_file)
        reload_data = storage.load(self.state_file)
        data = {}
        data['version'] = mopidy.__version__
        data['state'] = models.CoreState(
            tracklist=models.TracklistState(
                repeat=False, random=False,
                consume=False, single=False,
                next_tlid=1),
            history=models.HistoryState(),
            playback=models.PlaybackState(state='stopped',
                                          time_position=0),
            mixer=models.MixerState())
        assert data == reload_data

    def test_load_state_no_file(self):
        self.core.setup()

        assert self.core.mixer.get_mute() is None
        assert self.core.mixer.get_volume() is None
        assert self.core.tracklist._next_tlid == 1
        assert self.core.tracklist.get_repeat() is False
        assert self.core.tracklist.get_random() is False
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_single() is False
        assert self.core.tracklist.get_length() == 0
        assert self.core.playback._start_paused is False
        assert self.core.playback._start_at_position is None
        assert self.core.history.get_length() == 0

    def test_load_state_with_data(self):
        data = {}
        data['version'] = mopidy.__version__
        data['state'] = models.CoreState(
            tracklist=models.TracklistState(
                repeat=True, random=True,
                consume=False, single=False,
                tl_tracks=[models.TlTrack(tlid=12, track=Track(uri='a:a'))],
                next_tlid=14),
            history=models.HistoryState(history=[
                models.HistoryTrack(
                    timestamp=12,
                    track=models.Ref.track(uri='a:a', name='a')),
                models.HistoryTrack(
                    timestamp=13,
                    track=models.Ref.track(uri='a:b', name='b'))]),
            playback=models.PlaybackState(tlid=12, state='paused',
                                          time_position=432),
            mixer=models.MixerState(mute=True, volume=12))
        storage.dump(self.state_file, data)

        self.core.setup()

        assert self.core.mixer.get_mute() is True
        assert self.core.mixer.get_volume() == 12
        assert self.core.tracklist._next_tlid == 14
        assert self.core.tracklist.get_repeat() is True
        assert self.core.tracklist.get_random() is True
        assert self.core.tracklist.get_consume() is False
        assert self.core.tracklist.get_single() is False
        assert self.core.tracklist.get_length() == 1
        assert self.core.playback._start_paused is True
        assert self.core.playback._start_at_position == 432
        assert self.core.history.get_length() == 2

    def test_delete_state_file_on_restore(self):
        data = {}
        storage.dump(self.state_file, data)
        assert os.path.isfile(self.state_file)

        self.core.setup()

        assert not os.path.isfile(self.state_file)
