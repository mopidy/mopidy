from unittest import mock

import pykka
import pytest

from mopidy import core, mixer
from mopidy.core._state_storage import MixerControllerState
from tests import dummy_mixer


@pytest.fixture
def mixer_mock():
    return mock.Mock(spec=mixer.Mixer)


@pytest.fixture
def core_with_mixer_mock(mixer_mock):
    return core.Core(
        config={},
        mixer=mixer_mock,
        backends=[],
    )


def test_get_volume(core_with_mixer_mock, mixer_mock):
    mixer_mock.get_volume.return_value.get.return_value = 30

    assert core_with_mixer_mock.mixer.get_volume() == 30
    mixer_mock.get_volume.assert_called_once_with()


def test_set_volume(core_with_mixer_mock, mixer_mock):
    mixer_mock.set_volume.return_value.get.return_value = True
    core_with_mixer_mock.mixer.set_volume(30)

    mixer_mock.set_volume.assert_called_once_with(30)


def test_get_mute(core_with_mixer_mock, mixer_mock):
    mixer_mock.get_mute.return_value.get.return_value = True

    assert core_with_mixer_mock.mixer.get_mute() is True
    mixer_mock.get_mute.assert_called_once_with()


def test_set_mute(core_with_mixer_mock, mixer_mock):
    mixer_mock.set_mute.return_value.get.return_value = True
    core_with_mixer_mock.mixer.set_mute(True)

    mixer_mock.set_mute.assert_called_once_with(True)


@pytest.fixture
def core_without_mixer():
    return core.Core(
        config={},
        mixer=None,
        backends=[],
    )


def test_none_mixer_get_volume_return_none_because_it_is_unknown(
    core_without_mixer,
):
    assert core_without_mixer.mixer.get_volume() is None


def test_none_mixer_set_volume_return_false_because_it_failed(core_without_mixer):
    assert core_without_mixer.mixer.set_volume(30) is False


def test_none_mixer_get_mute_return_none_because_it_is_unknown(core_without_mixer):
    assert core_without_mixer.mixer.get_mute() is None


def test_none_mixer_set_mute_return_false_because_it_failed(core_without_mixer):
    assert core_without_mixer.mixer.set_mute(True) is False


@pytest.fixture
def send(mocker):
    return mocker.patch.object(mixer.MixerListener, "send")


@pytest.fixture
def mixer_proxy():
    yield dummy_mixer.create_proxy()
    pykka.ActorRegistry.stop_all()


@pytest.fixture
def core_with_mixer_proxy(mixer_proxy):
    return core.Core(
        config={},
        mixer=mixer_proxy,
        backends=[],
    )


def test_listener_forwards_mixer_volume_changed_event_to_frontends(
    core_with_mixer_proxy, send
):
    assert core_with_mixer_proxy.mixer.set_volume(volume=60) is True
    assert send.call_args[0][0] == "volume_changed"
    assert send.call_args[1]["volume"] == 60


def test_listener_forwards_mixer_mute_changed_event_to_frontends(
    core_with_mixer_proxy, send
):
    core_with_mixer_proxy.mixer.set_mute(mute=True)

    assert send.call_args[0][0] == "mute_changed"
    assert send.call_args[1]["mute"] is True


def test_none_mixer_listener_forwards_mixer_volume_changed_event_to_frontends(
    core_without_mixer, send
):
    assert core_without_mixer.mixer.set_volume(volume=60) is False
    assert send.call_count == 0


def test_none_mixer_listener_forwards_mixer_mute_changed_event_to_frontends(
    core_without_mixer, send
):
    core_without_mixer.mixer.set_mute(mute=True)
    assert send.call_count == 0


@pytest.fixture
def bad_mixer():
    bad_mixer = mock.Mock()
    bad_mixer.actor_ref.actor_class.__name__ = "DummyMixer"
    return bad_mixer


def test_get_volume_bad_backend_raises_exception(bad_mixer, core_without_mixer):
    bad_mixer.get_volume.return_value.get.side_effect = Exception
    assert core_without_mixer.mixer.get_volume() is None


def test_get_volume_bad_backend_returns_too_small_value(bad_mixer, core_without_mixer):
    bad_mixer.get_volume.return_value.get.return_value = -1
    assert core_without_mixer.mixer.get_volume() is None


def test_get_volume_bad_backend_returns_too_large_value(bad_mixer, core_without_mixer):
    bad_mixer.get_volume.return_value.get.return_value = 1000
    assert core_without_mixer.mixer.get_volume() is None


def test_get_volume_bad_backend_returns_wrong_type(bad_mixer, core_without_mixer):
    bad_mixer.get_volume.return_value.get.return_value = "12"
    assert core_without_mixer.mixer.get_volume() is None


def test_set_volume_bad_backend_raises_exception(bad_mixer, core_without_mixer):
    bad_mixer.set_volume.return_value.get.side_effect = Exception
    assert not core_without_mixer.mixer.set_volume(30)


def test_set_volume_bad_backend_returns_wrong_type(bad_mixer, core_without_mixer):
    bad_mixer.set_volume.return_value.get.return_value = "done"
    assert not core_without_mixer.mixer.set_volume(30)


def test_get_mute_bad_backend_raises_exception(bad_mixer, core_without_mixer):
    bad_mixer.get_mute.return_value.get.side_effect = Exception
    assert core_without_mixer.mixer.get_mute() is None


def test_get_mute_bad_backend_returns_wrong_type(bad_mixer, core_without_mixer):
    bad_mixer.get_mute.return_value.get.return_value = "12"
    assert core_without_mixer.mixer.get_mute() is None


def test_set_mute_bad_backend_raises_exception(bad_mixer, core_without_mixer):
    bad_mixer.set_mute.return_value.get.side_effect = Exception
    assert not core_without_mixer.mixer.set_mute(True)


def test_set_mute_bad_backend_returns_wrong_type(bad_mixer, core_without_mixer):
    bad_mixer.set_mute.return_value.get.return_value = "done"
    assert not core_without_mixer.mixer.set_mute(True)


def test_state_save_mute(core_with_mixer_proxy):
    volume = 32
    mute = False
    target = MixerControllerState(volume=volume, mute=mute)
    core_with_mixer_proxy.mixer.set_volume(volume)
    core_with_mixer_proxy.mixer.set_mute(mute)
    value = core_with_mixer_proxy.mixer._save_state()
    assert target == value


def test_state_save_unmute(core_with_mixer_proxy):
    volume = 33
    mute = True
    target = MixerControllerState(volume=volume, mute=mute)
    core_with_mixer_proxy.mixer.set_volume(volume)
    core_with_mixer_proxy.mixer.set_mute(mute)
    value = core_with_mixer_proxy.mixer._save_state()
    assert target == value


def test_state_load(core_with_mixer_proxy):
    core_with_mixer_proxy.mixer.set_volume(11)
    volume = 45
    target = MixerControllerState(volume=volume)
    coverage = ["mixer"]
    core_with_mixer_proxy.mixer._load_state(target, coverage)
    assert volume == core_with_mixer_proxy.mixer.get_volume()


def test_state_load_not_covered(core_with_mixer_proxy):
    core_with_mixer_proxy.mixer.set_volume(21)
    core_with_mixer_proxy.mixer.set_mute(True)
    target = MixerControllerState(volume=56, mute=False)
    coverage = ["other"]
    core_with_mixer_proxy.mixer._load_state(target, coverage)
    assert core_with_mixer_proxy.mixer.get_volume() == 21
    assert core_with_mixer_proxy.mixer.get_mute() is True


def test_state_load_mute_on(core_with_mixer_proxy):
    core_with_mixer_proxy.mixer.set_mute(False)
    assert core_with_mixer_proxy.mixer.get_mute() is False
    target = MixerControllerState(mute=True)
    coverage = ["mixer"]
    core_with_mixer_proxy.mixer._load_state(target, coverage)
    assert core_with_mixer_proxy.mixer.get_mute() is True


def test_state_load_mute_off(core_with_mixer_proxy):
    core_with_mixer_proxy.mixer.set_mute(True)
    assert core_with_mixer_proxy.mixer.get_mute() is True
    target = MixerControllerState(mute=False)
    coverage = ["mixer"]
    core_with_mixer_proxy.mixer._load_state(target, coverage)
    assert core_with_mixer_proxy.mixer.get_mute() is False


def test_state_load_invalid_type(core_with_mixer_proxy):
    with pytest.raises(TypeError):
        core_with_mixer_proxy.mixer._load_state(11, None)


def test_state_load_none(core_with_mixer_proxy):
    core_with_mixer_proxy.mixer._load_state(None, None)
