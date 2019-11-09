import unittest
from unittest import mock

import pykka

from mopidy import core, mixer
from mopidy.internal.models import MixerState

from tests import dummy_mixer


class CoreMixerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.mixer = mock.Mock(spec=mixer.Mixer)
        self.core = core.Core(mixer=self.mixer, backends=[])

    def test_get_volume(self):
        self.mixer.get_volume.return_value.get.return_value = 30

        assert self.core.mixer.get_volume() == 30
        self.mixer.get_volume.assert_called_once_with()

    def test_set_volume(self):
        self.mixer.set_volume.return_value.get.return_value = True
        self.core.mixer.set_volume(30)

        self.mixer.set_volume.assert_called_once_with(30)

    def test_get_mute(self):
        self.mixer.get_mute.return_value.get.return_value = True

        assert self.core.mixer.get_mute() is True
        self.mixer.get_mute.assert_called_once_with()

    def test_set_mute(self):
        self.mixer.set_mute.return_value.get.return_value = True
        self.core.mixer.set_mute(True)

        self.mixer.set_mute.assert_called_once_with(True)


class CoreNoneMixerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.core = core.Core(mixer=None, backends=[])

    def test_get_volume_return_none_because_it_is_unknown(self):
        assert self.core.mixer.get_volume() is None

    def test_set_volume_return_false_because_it_failed(self):
        assert self.core.mixer.set_volume(30) is False

    def test_get_mute_return_none_because_it_is_unknown(self):
        assert self.core.mixer.get_mute() is None

    def test_set_mute_return_false_because_it_failed(self):
        assert self.core.mixer.set_mute(True) is False


@mock.patch.object(mixer.MixerListener, "send")
class CoreMixerListenerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.mixer = dummy_mixer.create_proxy()
        self.core = core.Core(mixer=self.mixer, backends=[])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

    def test_forwards_mixer_volume_changed_event_to_frontends(self, send):
        assert self.core.mixer.set_volume(volume=60) is True
        assert send.call_args[0][0] == "volume_changed"
        assert send.call_args[1]["volume"] == 60

    def test_forwards_mixer_mute_changed_event_to_frontends(self, send):
        self.core.mixer.set_mute(mute=True)

        assert send.call_args[0][0] == "mute_changed"
        assert send.call_args[1]["mute"] is True


@mock.patch.object(mixer.MixerListener, "send")
class CoreNoneMixerListenerTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.core = core.Core(mixer=None, backends=[])

    def test_forwards_mixer_volume_changed_event_to_frontends(self, send):
        assert self.core.mixer.set_volume(volume=60) is False
        assert send.call_count == 0

    def test_forwards_mixer_mute_changed_event_to_frontends(self, send):
        self.core.mixer.set_mute(mute=True)
        assert send.call_count == 0


class MockBackendCoreMixerBase(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.mixer = mock.Mock()
        self.mixer.actor_ref.actor_class.__name__ = "DummyMixer"
        self.core = core.Core(mixer=self.mixer, backends=[])


class GetVolumeBadBackendTest(MockBackendCoreMixerBase):
    def test_backend_raises_exception(self):
        self.mixer.get_volume.return_value.get.side_effect = Exception
        assert self.core.mixer.get_volume() is None

    def test_backend_returns_too_small_value(self):
        self.mixer.get_volume.return_value.get.return_value = -1
        assert self.core.mixer.get_volume() is None

    def test_backend_returns_too_large_value(self):
        self.mixer.get_volume.return_value.get.return_value = 1000
        assert self.core.mixer.get_volume() is None

    def test_backend_returns_wrong_type(self):
        self.mixer.get_volume.return_value.get.return_value = "12"
        assert self.core.mixer.get_volume() is None


class SetVolumeBadBackendTest(MockBackendCoreMixerBase):
    def test_backend_raises_exception(self):
        self.mixer.set_volume.return_value.get.side_effect = Exception
        assert not self.core.mixer.set_volume(30)

    def test_backend_returns_wrong_type(self):
        self.mixer.set_volume.return_value.get.return_value = "done"
        assert not self.core.mixer.set_volume(30)


class GetMuteBadBackendTest(MockBackendCoreMixerBase):
    def test_backend_raises_exception(self):
        self.mixer.get_mute.return_value.get.side_effect = Exception
        assert self.core.mixer.get_mute() is None

    def test_backend_returns_wrong_type(self):
        self.mixer.get_mute.return_value.get.return_value = "12"
        assert self.core.mixer.get_mute() is None


class SetMuteBadBackendTest(MockBackendCoreMixerBase):
    def test_backend_raises_exception(self):
        self.mixer.set_mute.return_value.get.side_effect = Exception
        assert not self.core.mixer.set_mute(True)

    def test_backend_returns_wrong_type(self):
        self.mixer.set_mute.return_value.get.return_value = "done"
        assert not self.core.mixer.set_mute(True)


class CoreMixerSaveLoadStateTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.mixer = dummy_mixer.create_proxy()
        self.core = core.Core(mixer=self.mixer, backends=[])

    def test_save_mute(self):
        volume = 32
        mute = False
        target = MixerState(volume=volume, mute=mute)
        self.core.mixer.set_volume(volume)
        self.core.mixer.set_mute(mute)
        value = self.core.mixer._save_state()
        assert target == value

    def test_save_unmute(self):
        volume = 33
        mute = True
        target = MixerState(volume=volume, mute=mute)
        self.core.mixer.set_volume(volume)
        self.core.mixer.set_mute(mute)
        value = self.core.mixer._save_state()
        assert target == value

    def test_load(self):
        self.core.mixer.set_volume(11)
        volume = 45
        target = MixerState(volume=volume)
        coverage = ["mixer"]
        self.core.mixer._load_state(target, coverage)
        assert volume == self.core.mixer.get_volume()

    def test_load_not_covered(self):
        self.core.mixer.set_volume(21)
        self.core.mixer.set_mute(True)
        target = MixerState(volume=56, mute=False)
        coverage = ["other"]
        self.core.mixer._load_state(target, coverage)
        assert 21 == self.core.mixer.get_volume()
        assert self.core.mixer.get_mute() is True

    def test_load_mute_on(self):
        self.core.mixer.set_mute(False)
        assert self.core.mixer.get_mute() is False
        target = MixerState(mute=True)
        coverage = ["mixer"]
        self.core.mixer._load_state(target, coverage)
        assert self.core.mixer.get_mute() is True

    def test_load_mute_off(self):
        self.core.mixer.set_mute(True)
        assert self.core.mixer.get_mute() is True
        target = MixerState(mute=False)
        coverage = ["mixer"]
        self.core.mixer._load_state(target, coverage)
        assert self.core.mixer.get_mute() is False

    def test_load_invalid_type(self):
        with self.assertRaises(TypeError):
            self.core.mixer._load_state(11, None)

    def test_load_none(self):
        self.core.mixer._load_state(None, None)
