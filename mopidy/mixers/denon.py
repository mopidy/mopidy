import logging

from serial import Serial

from mopidy.mixers import BaseMixer
from mopidy.settings import MIXER_PORT

logger = logging.get_logger(u'mopidy.mixers.denon')

class DenonMixer(BaseMixer):
    def __init__(self):
        self._device = Serial(port=MIXER_PORT, timeout=0.2)
        self._levels = ['99']+["%(#)02d"% {'#': v} for v in range(0,99)]
        self._volume = 0

    def _get_volume(self):
        self.ensure_open_device()
        self._device.write('MV?\r')
        vol = self._device.read(20)[2:4]
        logger.debug(u'Volume: %s' % self._levels.index(vol))
        return self._levels.index(vol)

    def _set_volume(self, volume):
        # Clamp according to Denon-spec
        if volume > 99:
            volume = 99

        self.ensure_open_device()
        self._device.write('MV%s\r'% self._levels[volume])
        vol = self._device.read(20)[2:4]
        self._volume = self._levels.index(vol)
        logger.debug(u'Volume: %s' % self._volume)

    def ensure_open_device(self):
        if not self._device.isOpen():
            logger.debug(u'(re)connecting to Denon device')
            self._device.open()
