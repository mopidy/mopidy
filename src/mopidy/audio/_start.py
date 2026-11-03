from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mopidy.audio._gst import GstAudio

if TYPE_CHECKING:
    from mopidy.audio._api import AudioProxy
    from mopidy.config import Config
    from mopidy.mixer import MixerProxy


def start_audio_actor(*, config: Config, mixer: MixerProxy | None) -> AudioProxy:
    """Start the audio actor.

    Stop the actor with `actor_ref.stop()` on the returned proxy when you do
    not need it anymore.

    Args:
        config: The Mopidy config.
        mixer: The mixer to use, or `None` if there is no mixer.
    """
    return cast("AudioProxy", GstAudio.start(config=config, mixer=mixer).proxy())
