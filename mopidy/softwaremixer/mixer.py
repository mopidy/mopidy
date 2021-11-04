import logging

import pykka

from mopidy import mixer

logger = logging.getLogger(__name__)


class SoftwareMixer(pykka.ThreadingActor, mixer.Mixer):

    name = "software"

    def __init__(self, config):
        super().__init__(config)

        self._audio_mixer = None
        self._initial_volume = None
        self._initial_mute = None
        self._logical_volume = None

        self.min_volume = config["softwaremixer"]["min_volume"]
        self.max_volume = config["softwaremixer"]["max_volume"]
        self.volume_scale = config["softwaremixer"]["volume_scale"]
        self.volume_exp = config["softwaremixer"]["volume_exp"]

    def setup(self, mixer_ref):
        self._audio_mixer = mixer_ref

        # The Mopidy startup procedure will set the initial volume of a
        # mixer, but this happens before the audio actor's mixer is injected
        # into the software mixer actor and has no effect. Thus, we need to set
        # the initial volume again.
        if self._initial_volume is not None:
            self.set_volume(self._initial_volume)
        if self._initial_mute is not None:
            self.set_mute(self._initial_mute)

    def teardown(self):
        self._audio_mixer = None

    def get_volume(self):
        if self._audio_mixer is None:
            return None
        return int(self.mixer_volume_to_volume(self._audio_mixer.get_volume().get()))

    def set_volume(self, volume):
        self._logical_volume = self.volume_to_mixer_volume(volume)
        if self._audio_mixer is None:
            self._initial_volume = int(self._logical_volume)
            return False
        self._audio_mixer.set_volume(int(self._logical_volume))
        return True

    def mixer_volume_to_volume(self, mixer_volume):
        volume = mixer_volume
        if mixer_volume == int(self._logical_volume):
            # start calculation with exact original value to avoid
            # loss of precision from mixer/native conversions
            volume = self._logical_volume
        if self.volume_scale == "exp":
            coeff = pow(10, 2 * (self.volume_exp - 1))
            volume = pow(coeff * volume, 1/self.volume_exp)
        volume = (
            (volume - self.min_volume)
            * 100.0
            / (self.max_volume - self.min_volume)
        )
        return volume

    def volume_to_mixer_volume(self, volume):
        mixer_volume = (
            self.min_volume
            + volume * (self.max_volume - self.min_volume) / 100.0
        )
        if self.volume_scale == "exp":
            coeff = pow(10, 2 * (self.volume_exp - 1))
            mixer_volume = pow(mixer_volume, self.volume_exp) / coeff
        return mixer_volume

    def get_mute(self):
        if self._audio_mixer is None:
            return None
        return self._audio_mixer.get_mute().get()

    def set_mute(self, mute):
        if self._audio_mixer is None:
            self._initial_mute = mute
            return False
        self._audio_mixer.set_mute(mute)
        return True
