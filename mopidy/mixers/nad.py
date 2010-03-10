import logging
from serial import Serial
from multiprocessing import Process, Pipe

from mopidy.mixers import BaseMixer
from mopidy.settings import MIXER_PORT

logger = logging.getLogger('mopidy.mixers.nad')

class NadMixer(BaseMixer):
    """
    The NAD mixer was created using a NAD C 355BEE amplifier, but should also
    work with other NAD amplifiers supporting the same RS-232 protocol. The C
    355BEE does not give you access to the current volume. It only supports
    increasing or decreasing the volume one step at the time. Other NAD
    amplifiers may support more advanced volume adjustment than what is
    currently used by this mixer.

    Sadly, this means that if you use the remote control to change the volume
    on the amplifier, Mopidy will no longer report the correct volume. To
    recalibrate the mixer, set the volume to 0, and then back again to the
    level you want.
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
            self._pipe.send({'command': 'calibrate'})
        self._pipe.send({'command': 'set_volume', 'volume': volume})


class NadTalker(Process):
    #: Number of volume levels the device supports
    NUM_STEPS = 40

    #: Volume in range [0..NUM_STEPS]. :class:`None` before calibration.
    _nad_volume = None

    def __init__(self, pipe=None):
        Process.__init__(self)
        self.pipe = pipe

    def run(self):
        # If you set the timeout too low, the reads will never get complete
        # confirmations and calibration will decrease volume forever.
        self._device = Serial(port=MIXER_PORT, baudrate=115200, timeout=0.2)
        self._clear()
        self._device_model = self._get_device_model()
        self._calibrate()
        while self.pipe.poll(None):
            message = self.pipe.recv()
            if message['command'] == 'set_volume':
                self._set_volume(message['volume'])
            elif message['command'] == 'calibrate':
                self._calibrate()

    def _get_device_model(self):
        self._write('Main.Model?')
        result = ''
        while len(result) < 2:
            result = self._readline()
        result = result.replace('Main.Model=', '')
        logger.info(u'Connected to device of model "%s"' % result)
        return result

    def _calibrate(self):
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
        logger.info(u'Calibration of NAD amplifier done')

    def _set_volume(self, volume):
        logger.debug(u'Setting volume to %d' % volume)
        self._set_nad_volume(int(round(volume * self.NUM_STEPS / 100.0)))

    def _set_nad_volume(self, target_volume):
        """
        Increase or decrease the amplifier volume until it matches the given
        target volume. Only calls to increase and decrease that returns
        :class:`True` are counted against the internal volume.
        """
        if self._nad_volume is None:
            raise Exception(u'Calibration needed')
        while target_volume > self._nad_volume:
            if self._increase_volume():
                self._nad_volume += 1
        while target_volume < self._nad_volume:
            if self._decrease_volume():
                self._nad_volume -= 1

    def _increase_volume(self):
        self._write('Main.Volume+')
        return self._readline() == 'Main.Volume+'

    def _decrease_volume(self):
        self._write('Main.Volume-')
        return self._readline() == 'Main.Volume-'

    def _clear(self):
        """Clear input and output buffers."""
        self._device.flushInput()
        self._device.flushOutput()

    def _write(self, data):
        """Write and flush data to device."""
        if not self._device.isOpen():
            self._device.open()
        self._device.write('\r%s\r' % data)
        self._device.flush()

    def _readline(self):
        """
        Read line from device. The result is stripped for leading and trailing
        whitespace.
        """
        if not self._device.isOpen():
            self._device.open()
        result = self._device.readline(eol='\r')
        return result.strip()
