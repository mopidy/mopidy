from pytest_mock import MockFixture

from mopidy import mixer
from mopidy.types import Percentage


def test_mixer_listener_on_event_forwards_to_specific_handler(mocker: MockFixture):
    listener = mixer.MixerListener()
    mock = mocker.patch.object(listener, "volume_changed")

    listener.on_event("volume_changed", volume=60)

    mock.assert_called_with(volume=60)


def test_listener_has_default_impl_for_volume_changed():
    listener = mixer.MixerListener()

    listener.volume_changed(volume=Percentage(60))


def test_listener_has_default_impl_for_mute_changed():
    listener = mixer.MixerListener()

    listener.mute_changed(mute=True)
