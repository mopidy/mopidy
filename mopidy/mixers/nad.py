import logging
from serial import Serial
from multiprocessing import Pipe, Process

from mopidy.mixers import BaseMixer
from mopidy.settings import MIXER_PORT

logger = logging.getLogger('mopidy.mixers.nad')

class NadMixer(BaseMixer):
    """
    The NAD mixer was created using a NAD C 355BEE amplifier, but should also
    work with other NAD amplifiers supporting the same RS-232 protocol (v2.x).
    The C 355BEE does not give you access to the current volume. It only
    supports increasing or decreasing the volume one step at the time. Other
    NAD amplifiers may support more advanced volume adjustment than what is
    currently used by this mixer.

    Sadly, this means that if you use the remote control to change the volume
    on the amplifier, Mopidy will no longer report the correct volume. To
    recalibrate the mixer, set the volume to 0, and then back again to the
    level you want. This will reset the amplifier to a known state, including
    powering on the device, selecting the configured speakers and input
    sources.
    """

    def __init__(self):
        self._volume = None
        self._pipe, other_end = Pipe()
        NadTalker(pipe=other_end).start()

    def _get_volume(self):
        return self._volume

    def _set_volume(self, volume):
        self._volume = volume
        if volume == 0:
            self._pipe.send({'command': 'reset_device'})
        self._pipe.send({'command': 'set_volume', 'volume': volume})


class NadTalker(Process):
    #: Timeout in seconds used for read/write operations.
    #:
    #: If you set the timeout too low, the reads will never get complete
    #: confirmations and calibration will decrease volume forever. If you set
    #: the timeout too high, stuff takes more time.
    TIMEOUT = 0.2

    #: Number of volume levels the device supports
    NUM_STEPS = 40

    #: The amplifier source to use
    SOURCE = 'Aux'

    #: State of speakers A
    SPEAKERS_A = 'On'

    #: State of speakers B
    SPEAKERS_B = 'Off'

    #: Volume in range [0..NUM_STEPS]. :class:`None` before calibration.
    _nad_volume = None

    def __init__(self, pipe=None):
        Process.__init__(self)
        self.pipe = pipe

    def run(self):
        self._open_connection()
        self._set_device_to_known_state()
        while self.pipe.poll(None):
            message = self.pipe.recv()
            if message['command'] == 'set_volume':
                self._set_volume(message['volume'])
            elif message['command'] == 'reset_device':
                self._set_device_to_known_state()

    def _open_connection(self):
        """
        Opens serial connection to the device.

        Communication settings: 115200 bps 8N1
        """
        self._device = Serial(port=MIXER_PORT, baudrate=115200,
            timeout=self.TIMEOUT)
        self._get_device_model()

    def _set_device_to_known_state(self):
        self._power_device_on()
        self._select_speakers()
        self._select_input_source()
        self._unmute()
        self._calibrate_volume()

    def _get_device_model(self):
        model = self._ask_device('Main.Model')
        logger.info(u'Connected to device of model "%s"' % model)
        return model

    def _power_device_on(self):
        while self._ask_device('Main.Power') != 'On':
            logger.info(u'Powering device on')
            self._command_device('Main.Power', 'On')

    def _select_speakers(self):
        while self._ask_device('Main.SpeakerA') != self.SPEAKERS_A:
            logger.info(u'Setting speakers A "%s"', self.SPEAKERS_A)
            self._command_device('Main.SpeakerA', self.SPEAKERS_A)
        while self._ask_device('Main.SpeakerB') != self.SPEAKERS_B:
            logger.info(u'Setting speakers B "%s"', self.SPEAKERS_B)
            self._command_device('Main.SpeakerB', self.SPEAKERS_B)

    def _select_input_source(self):
        while self._ask_device('Main.Source') != self.SOURCE:
            logger.info(u'Selecting input source "%s"', self.SOURCE)
            self._command_device('Main.Source', self.SOURCE)

    def _unmute(self):
        while self._ask_device('Main.Mute') != 'Off':
            logger.info(u'Unmuting device')
            self._command_device('Main.Mute', 'Off')

    def _ask_device(self, key):
        self._write('%s?' % key)
        return self._readline().replace('%s=' % key, '')

    def _command_device(self, key, value):
        self._write('%s=%s' % (key, value))
        self._readline()

    def _calibrate_volume(self):
        """
        The NAD C 355BEE amplifier has 40 different volume levels. We have no
        way of asking on which level we are. Thus, we must calibrate the mixer
        by decreasing the volume 39 times.
        """
        logger.info(u'Calibrating NAD amplifier')
        steps_left = self.NUM_STEPS - 1
        while steps_left:
            if self._decrease_volume():
                steps_left -= 1
        self._nad_volume = 0
        logger.info(u'Done calibrating NAD amplifier')

    def _set_volume(self, volume):
        """
        Increase or decrease the amplifier volume until it matches the given
        target volume.
        """
        logger.debug(u'Setting volume to %d' % volume)
        target_nad_volume = int(round(volume * self.NUM_STEPS / 100.0))
        if self._nad_volume is None:
            return # Calibration needed
        while target_nad_volume > self._nad_volume:
            if self._increase_volume():
                self._nad_volume += 1
        while target_nad_volume < self._nad_volume:
            if self._decrease_volume():
                self._nad_volume -= 1

    def _increase_volume(self):
        self._write('Main.Volume+')
        return self._readline() == 'Main.Volume+'

    def _decrease_volume(self):
        self._write('Main.Volume-')
        return self._readline() == 'Main.Volume-'

    def _write(self, data):
        """
        Write data to device.

        Prepends and appends a newline to the data, as recommended by the NAD
        documentation.
        """
        if not self._device.isOpen():
            self._device.open()
        self._device.write('\n%s\n' % data)
        logger.debug('Write: %s', data)

    def _readline(self):
        """
        Read line from device. The result is stripped for leading and trailing
        whitespace.
        """
        if not self._device.isOpen():
            self._device.open()
        result = self._device.readline(eol='\n').strip()
        if result:
            logger.debug('Read: %s', result)
        return result
