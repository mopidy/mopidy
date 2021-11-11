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

        self.config = config
        self.min_volume = self.config["softwaremixer"]["min_volume"]
        self.max_volume = self.config["softwaremixer"]["max_volume"]
        self.volume_scale = self.config["softwaremixer"]["volume_scale"]
        self.volume_exp = self.config["softwaremixer"]["volume_exp"]

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
        mixer_volume = self._audio_mixer.get_volume().get()
        if mixer_volume == round(self._logical_volume):
            mixer_volume = self._logical_volume
        volume = self.volume_filter_out(mixer_volume)
        return round(volume)

    def set_volume(self, volume):
        if self._audio_mixer is None:
            self._initial_volume = volume
            return False
        self._logical_volume = self.volume_filter_in(volume)
        self._audio_mixer.set_volume(round(self._logical_volume))
        return True

    def volume_filter_in(self, volume):
        mixer_volume = volume
        if self.volume_scale == "exp":
            coeff = pow(10, 2 * (self.volume_exp - 1))
            mixer_volume = pow(mixer_volume, self.volume_exp) / coeff
        mixer_volume = (
            self.min_volume
            + mixer_volume * (self.max_volume - self.min_volume) / 100.0
        )
        return mixer_volume

    def volume_filter_out(self, volume):
        ui_volume = volume
        if volume == round(self._logical_volume):
            # start calculation with exact original value to avoid
            # loss of precision from mixer/native conversions
            ui_volume = self._logical_volume
        ui_volume = (
            (ui_volume - self.min_volume)
            * 100.0
            / (self.max_volume - self.min_volume)
        )
        if self.volume_scale == "exp":
            coeff = pow(10, 2 * (self.volume_exp - 1))
            ui_volume = pow(coeff * ui_volume, 1/self.volume_exp)
        return ui_volume

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
