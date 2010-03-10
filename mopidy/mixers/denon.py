from serial import Serial

from mopidy.mixers import BaseMixer
from mopidy.settings import MIXER_PORT


class DenonMixer(BaseMixer):
    def __init__(self):
        self._device = Serial(port=MIXER_PORT)
        self._levels = ['99']+["%(#)02d"% {'#': v} for v in range(0,99)]
        self._volume = None

    def _get_volume(self):
        # The Denon spec doesnt seem to document
        # how to query the volume, so we keep the
        # state internally
        return self._volume

    def _set_volume(self, volume):
        # Clamp according to Denon-spec
        if not volume:
            volume = 0
        elif volume > 99:
            volume = 99

        self._volume = volume
        self._device.write('MV%s\r'% self._levels[volume])
