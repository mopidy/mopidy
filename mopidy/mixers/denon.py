import logging

from serial import Serial

from mopidy.mixers import BaseMixer
from mopidy.settings import MIXER_PORT

logger = logging.get_logger(u'mopidy.mixers.denon')

class DenonMixer(BaseMixer):
    def __init__(self):
        self._device = Serial(port=MIXER_PORT, timeout=0.2)
        self._levels = ['99']+["%(#)02d"% {'#': v} for v in range(0,99)]
        self._volume = None

    def _get_volume(self):
        self._device.write('MV?\r')
        vol = self._device.read(20)[2:4]
        logger.debug(u'Volume: %s' % self._levels.index(vol))
        return self._levels.index(vol)

    def _set_volume(self, volume):
        # Clamp according to Denon-spec
        if not volume:
            volume = 0
        elif volume > 99:
            volume = 99

        if not self._device.isOpen():
            self._device.open()
        self._device.write('MV%s\r'% self._levels[volume])
        vol = self._device.read(20)[2:4]
        self._volume = self._levels.index(vol)
