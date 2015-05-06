from __future__ import absolute_import, unicode_literals

import unittest

import mock

import pykka

from mopidy import core, mixer
from tests import dummy_mixer


class CoreMixerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.mixer = mock.Mock(spec=mixer.Mixer)
        self.core = core.Core(mixer=self.mixer, backends=[])

    def test_get_volume(self):
        self.mixer.get_volume.return_value.get.return_value = 30

        self.assertEqual(self.core.mixer.get_volume(), 30)
        self.mixer.get_volume.assert_called_once_with()

    def test_set_volume(self):
        self.mixer.set_volume.return_value.get.return_value = True
        self.core.mixer.set_volume(30)

        self.mixer.set_volume.assert_called_once_with(30)

    def test_get_mute(self):
        self.mixer.get_mute.return_value.get.return_value = True

        self.assertEqual(self.core.mixer.get_mute(), True)
        self.mixer.get_mute.assert_called_once_with()

    def test_set_mute(self):
        self.mixer.set_mute.return_value.get.return_value = True
        self.core.mixer.set_mute(True)

        self.mixer.set_mute.assert_called_once_with(True)


class CoreNoneMixerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.core = core.Core(mixer=None, backends=[])

    def test_get_volume_return_none_because_it_is_unknown(self):
        self.assertEqual(self.core.mixer.get_volume(), None)

    def test_set_volume_return_false_because_it_failed(self):
        self.assertEqual(self.core.mixer.set_volume(30), False)

    def test_get_mute_return_none_because_it_is_unknown(self):
        self.assertEqual(self.core.mixer.get_mute(), None)

    def test_set_mute_return_false_because_it_failed(self):
        self.assertEqual(self.core.mixer.set_mute(True), False)


@mock.patch.object(mixer.MixerListener, 'send')
class CoreMixerListenerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.mixer = dummy_mixer.create_proxy()
        self.core = core.Core(mixer=self.mixer, backends=[])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def test_forwards_mixer_volume_changed_event_to_frontends(self, send):
        self.assertEqual(self.core.mixer.set_volume(volume=60), True)
        self.assertEqual(send.call_args[0][0], 'volume_changed')
        self.assertEqual(send.call_args[1]['volume'], 60)

    def test_forwards_mixer_mute_changed_event_to_frontends(self, send):
        self.core.mixer.set_mute(mute=True)

        self.assertEqual(send.call_args[0][0], 'mute_changed')
        self.assertEqual(send.call_args[1]['mute'], True)


@mock.patch.object(mixer.MixerListener, 'send')
class CoreNoneMixerListenerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.core = core.Core(mixer=None, backends=[])

    def test_forwards_mixer_volume_changed_event_to_frontends(self, send):
        self.assertEqual(self.core.mixer.set_volume(volume=60), False)
        self.assertEqual(send.call_count, 0)

    def test_forwards_mixer_mute_changed_event_to_frontends(self, send):
        self.core.mixer.set_mute(mute=True)
        self.assertEqual(send.call_count, 0)


class MockBackendCoreMixerBase(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.mixer = mock.Mock()
        self.mixer.actor_ref.actor_class.__name__ = 'DummyMixer'
        self.core = core.Core(mixer=self.mixer, backends=[])


class GetVolumeBadBackendTest(MockBackendCoreMixerBase):

    def test_backend_raises_exception(self):
        self.mixer.get_volume.return_value.get.side_effect = Exception
        self.assertEqual(self.core.mixer.get_volume(), None)

    def test_backend_returns_too_small_value(self):
        self.mixer.get_volume.return_value.get.return_value = -1
        self.assertEqual(self.core.mixer.get_volume(), None)

    def test_backend_returns_too_large_value(self):
        self.mixer.get_volume.return_value.get.return_value = 1000
        self.assertEqual(self.core.mixer.get_volume(), None)

    def test_backend_returns_wrong_type(self):
        self.mixer.get_volume.return_value.get.return_value = '12'
        self.assertEqual(self.core.mixer.get_volume(), None)


class SetVolumeBadBackendTest(MockBackendCoreMixerBase):

    def test_backend_raises_exception(self):
        self.mixer.set_volume.return_value.get.side_effect = Exception
        self.assertFalse(self.core.mixer.set_volume(30))

    def test_backend_returns_wrong_type(self):
        self.mixer.set_volume.return_value.get.return_value = 'done'
        self.assertFalse(self.core.mixer.set_volume(30))


class GetMuteBadBackendTest(MockBackendCoreMixerBase):

    def test_backend_raises_exception(self):
        self.mixer.get_mute.return_value.get.side_effect = Exception
        self.assertEqual(self.core.mixer.get_mute(), None)

    def test_backend_returns_wrong_type(self):
        self.mixer.get_mute.return_value.get.return_value = '12'
        self.assertEqual(self.core.mixer.get_mute(), None)


class SetMuteBadBackendTest(MockBackendCoreMixerBase):

    def test_backend_raises_exception(self):
        self.mixer.set_mute.return_value.get.side_effect = Exception
        self.assertFalse(self.core.mixer.set_mute(True))

    def test_backend_returns_wrong_type(self):
        self.mixer.set_mute.return_value.get.return_value = 'done'
        self.assertFalse(self.core.mixer.set_mute(True))
