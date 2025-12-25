from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pykka
from pykka.typing import proxy_method

from mopidy import mixer

if TYPE_CHECKING:
    from mopidy.audio._gst import GstSoftwareMixerAdapterProxy
    from mopidy.config import Config
    from mopidy.types import Percentage

logger = logging.getLogger(__name__)


class SoftwareMixer(pykka.ThreadingActor, mixer.Mixer):
    name = "software"

    def __init__(self, config: Config) -> None:
        super().__init__(config)

        self._gst_mixer: GstSoftwareMixerAdapterProxy | None = None
        self._initial_volume: Percentage | None = None
        self._initial_mute: bool | None = None

    def setup(self, gst_mixer: GstSoftwareMixerAdapterProxy) -> None:
        self._gst_mixer = gst_mixer

        # The Mopidy startup procedure will set the initial volume of a
        # mixer, but this happens before the audio actor's mixer is injected
        # into the software mixer actor and has no effect. Thus, we need to set
        # the initial volume again.
        if self._initial_volume is not None:
            self.set_volume(self._initial_volume)
        if self._initial_mute is not None:
            self.set_mute(self._initial_mute)

    def teardown(self) -> None:
        self._gst_mixer = None

    def get_volume(self) -> Percentage | None:
        if self._gst_mixer is None:
            return None
        return self._gst_mixer.get_volume().get()

    def set_volume(self, volume: Percentage) -> bool:
        if self._gst_mixer is None:
            self._initial_volume = volume
            return False
        self._gst_mixer.set_volume(volume)
        return True

    def get_mute(self) -> bool | None:
        if self._gst_mixer is None:
            return None
        return self._gst_mixer.get_mute().get()

    def set_mute(self, mute: bool) -> bool:
        if self._gst_mixer is None:
            self._initial_mute = mute
            return False
        self._gst_mixer.set_mute(mute)
        return True


class SoftwareMixerProxy(mixer.MixerProxy):
    setup = proxy_method(SoftwareMixer.setup)
    teardown = proxy_method(SoftwareMixer.teardown)
