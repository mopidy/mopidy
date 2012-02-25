import logging
import serial

from pykka.actor import ThreadingActor

from mopidy import settings
from mopidy.mixers.base import BaseMixer

logger = logging.getLogger('mopidy.mixers.nad')

class NadMixer(ThreadingActor, BaseMixer):
    """
    Mixer for controlling NAD amplifiers and receivers using the NAD RS-232
    protocol.

    The NAD mixer was created using a NAD C 355BEE amplifier, but should also
    work with other NAD amplifiers supporting the same RS-232 protocol (v2.x).
    The C 355BEE does not give you access to the current volume. It only
    supports increasing or decreasing the volume one step at the time. Other
    NAD amplifiers may support more advanced volume adjustment than what is
    currently used by this mixer.

    Sadly, this means that if you use the remote control to change the volume
    on the amplifier, Mopidy will no longer report the correct volume.

    **Dependencies**

    - pyserial (python-serial on Debian/Ubuntu)

    **Settings**

    - :attr:`mopidy.settings.MIXER_EXT_PORT` -- Example: ``/dev/ttyUSB0``
    - :attr:`mopidy.settings.MIXER_EXT_SOURCE` -- Example: ``Aux``
    - :attr:`mopidy.settings.MIXER_EXT_SPEAKERS_A` -- Example: ``On``
    - :attr:`mopidy.settings.MIXER_EXT_SPEAKERS_B` -- Example: ``Off``

    """

    def __init__(self):
        super(NadMixer, self).__init__()
        self._volume_cache = None
        self._nad_talker = NadTalker.start().proxy()

    def get_volume(self):
        return self._volume_cache

    def set_volume(self, volume):
        self._volume_cache = volume
        self._nad_talker.set_volume(volume)


class NadTalker(ThreadingActor):
    """
    Independent process which does the communication with the NAD device.

    Since the communication is done in an independent process, Mopidy won't
    block other requests while doing rather time consuming work like
    calibrating the NAD device's volume.
    """

    # Timeout in seconds used for read/write operations.
    # If you set the timeout too low, the reads will never get complete
    # confirmations and calibration will decrease volume forever. If you set
    # the timeout too high, stuff takes more time. 0.2s seems like a good value
    # for NAD C 355BEE.
    TIMEOUT = 0.2

    # Number of volume levels the device supports. 40 for NAD C 355BEE.
    VOLUME_LEVELS = 40

    # Volume in range 0..VOLUME_LEVELS. :class:`None` before calibration.
    _nad_volume = None

    def __init__(self):
        super(NadTalker, self).__init__()
        self._device = None

    def on_start(self):
        self._open_connection()
        self._set_device_to_known_state()

    def _open_connection(self):
        # Opens serial connection to the device.
        # Communication settings: 115200 bps 8N1
        logger.info(u'Connecting to serial device "%s"',
            settings.MIXER_EXT_PORT)
        self._device = serial.Serial(port=settings.MIXER_EXT_PORT,
            baudrate=115200, timeout=self.TIMEOUT)
        self._get_device_model()

    def _set_device_to_known_state(self):
        self._power_device_on()
        self._select_speakers()
        self._select_input_source()
        self._unmute()
        self._calibrate_volume()

    def _get_device_model(self):
        model = self._ask_device('Main.Model')
        logger.info(u'Connected to device of model "%s"', model)
        return model

    def _power_device_on(self):
        while self._ask_device('Main.Power') != 'On':
            logger.info(u'Powering device on')
            self._command_device('Main.Power', 'On')

    def _select_speakers(self):
        if settings.MIXER_EXT_SPEAKERS_A is not None:
            while (self._ask_device('Main.SpeakerA')
                    != settings.MIXER_EXT_SPEAKERS_A):
                logger.info(u'Setting speakers A "%s"',
                    settings.MIXER_EXT_SPEAKERS_A)
                self._command_device('Main.SpeakerA',
                    settings.MIXER_EXT_SPEAKERS_A)
        if settings.MIXER_EXT_SPEAKERS_B is not None:
            while (self._ask_device('Main.SpeakerB') !=
                    settings.MIXER_EXT_SPEAKERS_B):
                logger.info(u'Setting speakers B "%s"',
                    settings.MIXER_EXT_SPEAKERS_B)
                self._command_device('Main.SpeakerB',
                    settings.MIXER_EXT_SPEAKERS_B)

    def _select_input_source(self):
        if settings.MIXER_EXT_SOURCE is not None:
            while self._ask_device('Main.Source') != settings.MIXER_EXT_SOURCE:
                logger.info(u'Selecting input source "%s"',
                    settings.MIXER_EXT_SOURCE)
                self._command_device('Main.Source', settings.MIXER_EXT_SOURCE)

    def _unmute(self):
        while self._ask_device('Main.Mute') != 'Off':
            logger.info(u'Unmuting device')
            self._command_device('Main.Mute', 'Off')

    def _ask_device(self, key):
        self._write('%s?' % key)
        return self._readline().replace('%s=' % key, '')

    def _command_device(self, key, value):
        if type(value) == unicode:
            value = value.encode('utf-8')
        self._write('%s=%s' % (key, value))
        self._readline()

    def _calibrate_volume(self):
        # The NAD C 355BEE amplifier has 40 different volume levels. We have no
        # way of asking on which level we are. Thus, we must calibrate the
        # mixer by decreasing the volume 39 times.
        logger.info(u'Calibrating NAD amplifier')
        steps_left = self.VOLUME_LEVELS - 1
        while steps_left:
            if self._decrease_volume():
                steps_left -= 1
        self._nad_volume = 0
        logger.info(u'Done calibrating NAD amplifier')

    def set_volume(self, volume):
        # Increase or decrease the amplifier volume until it matches the given
        # target volume.
        logger.debug(u'Setting volume to %d' % volume)
        target_nad_volume = int(round(volume * self.VOLUME_LEVELS / 100.0))
        if self._nad_volume is None:
            return # Calibration needed
        while target_nad_volume > self._nad_volume:
            if self._increase_volume():
                self._nad_volume += 1
        while target_nad_volume < self._nad_volume:
            if self._decrease_volume():
                self._nad_volume -= 1

    def _increase_volume(self):
        # Increase volume. Returns :class:`True` if confirmed by device.
        self._write('Main.Volume+')
        return self._readline() == 'Main.Volume+'

    def _decrease_volume(self):
        # Decrease volume. Returns :class:`True` if confirmed by device.
        self._write('Main.Volume-')
        return self._readline() == 'Main.Volume-'

    def _write(self, data):
        # Write data to device. Prepends and appends a newline to the data, as
        # recommended by the NAD documentation.
        if not self._device.isOpen():
            self._device.open()
        self._device.write('\n%s\n' % data)
        logger.debug('Write: %s', data)

    def _readline(self):
        # Read line from device. The result is stripped for leading and
        # trailing whitespace.
        if not self._device.isOpen():
            self._device.open()
        result = self._device.readline().strip()
        if result:
            logger.debug('Read: %s', result)
        return result
