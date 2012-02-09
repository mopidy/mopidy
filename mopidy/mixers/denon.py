import logging

from pykka.actor import ThreadingActor

from mopidy import settings
from mopidy.mixers.base import BaseMixer

logger = logging.getLogger(u'mopidy.mixers.denon')

class DenonMixer(ThreadingActor, BaseMixer):
    """
    Mixer for controlling Denon amplifiers and receivers using the RS-232
    protocol.

    The external mixer is the authoritative source for the current volume.
    This allows the user to use his remote control the volume without Mopidy
    cancelling the volume setting.

    **Dependencies**

    - pyserial (python-serial on Debian/Ubuntu)

    **Settings**

    - :attr:`mopidy.settings.MIXER_EXT_PORT` -- Example: ``/dev/ttyUSB0``
    """

    def __init__(self, device=None):
        super(DenonMixer, self).__init__()
        self._device = device
        self._levels = ['99'] + ["%(#)02d" % {'#': v} for v in range(0, 99)]
        self._volume = 0

    def on_start(self):
        if self._device is None:
            from serial import Serial
            self._device = Serial(port=settings.MIXER_EXT_PORT, timeout=0.2)

    def get_volume(self):
        self._ensure_open_device()
        self._device.write('MV?\r')
        vol = str(self._device.readline()[2:4])
        logger.debug(u'_get_volume() = %s' % vol)
        return self._levels.index(vol)

    def set_volume(self, volume):
        # Clamp according to Denon-spec
        if volume > 99:
            volume = 99
        self._ensure_open_device()
        self._device.write('MV%s\r'% self._levels[volume])
        vol = self._device.readline()[2:4]
        self._volume = self._levels.index(vol)

    def _ensure_open_device(self):
        if not self._device.isOpen():
            logger.debug(u'(re)connecting to Denon device')
            self._device.open()
