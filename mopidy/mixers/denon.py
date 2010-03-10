import logging
from threading import Lock

from serial import Serial

from mopidy.mixers import BaseMixer
from mopidy.settings import MIXER_PORT

logger = logging.getLogger(u'mopidy.mixers.denon')

class DenonMixer(BaseMixer):
    def __init__(self):
        self._device = Serial(port=MIXER_PORT, timeout=0.2)
        self._levels = ['99']+["%(#)02d"% {'#': v} for v in range(0,99)]
        self._volume = 0
        self._lock = Lock()

    def _get_volume(self):
        self._lock.acquire();
        self.ensure_open_device()
        self._device.write('MV?\r')
        vol = str(self._device.readline()[2:4])
        self._lock.release()
        logger.debug(u'_get_volume() = %s' % vol)
        return self._levels.index(vol)

    def _set_volume(self, volume):
        volume = int(volume)
        # Clamp according to Denon-spec
        if volume > 99:
            volume = 99
        self._lock.acquire()
        self.ensure_open_device()
        self._device.write('MV%s\r'% self._levels[volume])
        vol = self._device.readline()[2:4]
        self._lock.release()
        self._volume = self._levels.index(vol)

    def ensure_open_device(self):
        if not self._device.isOpen():
            logger.debug(u'(re)connecting to Denon device')
            self._device.open()
