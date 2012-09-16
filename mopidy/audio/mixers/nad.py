import logging

import pygst
pygst.require('0.10')
import gobject
import gst

try:
    import serial
except ImportError:
    serial = None

from pykka.actor import ThreadingActor

from mopidy.audio.mixers import create_track


logger = logging.getLogger('mopidy.audio.mixers.nad')


class NadMixer(gst.Element, gst.ImplementsInterface, gst.interfaces.Mixer):
    __gstdetails__ = ('NadMixer',
                      'Mixer',
                      'Mixer to control NAD amplifiers using a serial link',
                      'Stein Magnus Jodal')

    port = gobject.property(type=str, default='/dev/ttyUSB0')
    source = gobject.property(type=str)
    speakers_a = gobject.property(type=str)
    speakers_b = gobject.property(type=str)

    def __init__(self):
        gst.Element.__init__(self)
        self._volume_cache = 0
        self._nad_talker = None

    def list_tracks(self):
        track = create_track(
            label='Master',
            initial_volume=0,
            min_volume=0,
            max_volume=100,
            num_channels=1,
            flags=(gst.interfaces.MIXER_TRACK_MASTER |
                 gst.interfaces.MIXER_TRACK_OUTPUT))
        return [track]

    def get_volume(self, track):
        return [self._volume_cache]

    def set_volume(self, track, volumes):
        if len(volumes):
            volume = volumes[0]
            self._volume_cache = volume
            self._nad_talker.set_volume(volume)

    def set_mute(self, track, mute):
        self._nad_talker.mute(mute)

    def do_change_state(self, transition):
        if transition == gst.STATE_CHANGE_NULL_TO_READY:
            if serial is None:
                logger.warning(u'nadmixer dependency python-serial not found')
                return gst.STATE_CHANGE_FAILURE
            self._start_nad_talker()
        return gst.STATE_CHANGE_SUCCESS

    def _start_nad_talker(self):
        self._nad_talker = NadTalker.start(
            port=self.port,
            source=self.source or None,
            speakers_a=self.speakers_a or None,
            speakers_b=self.speakers_b or None
        ).proxy()


gobject.type_register(NadMixer)
gst.element_register(NadMixer, 'nadmixer', gst.RANK_MARGINAL)


class NadTalker(ThreadingActor):
    """
    Independent thread which does the communication with the NAD amplifier

    Since the communication is done in an independent thread, Mopidy won't
    block other requests while doing rather time consuming work like
    calibrating the NAD amplifier's volume.
    """

    # Serial link settings
    BAUDRATE = 115200
    BYTESIZE = 8
    PARITY = 'N'
    STOPBITS = 1

    # Timeout in seconds used for read/write operations.
    # If you set the timeout too low, the reads will never get complete
    # confirmations and calibration will decrease volume forever. If you set
    # the timeout too high, stuff takes more time. 0.2s seems like a good value
    # for NAD C 355BEE.
    TIMEOUT = 0.2

    # Number of volume levels the amplifier supports. 40 for NAD C 355BEE.
    VOLUME_LEVELS = 40

    def __init__(self, port, source, speakers_a, speakers_b):
        super(NadTalker, self).__init__()

        self.port = port
        self.source = source
        self.speakers_a = speakers_a
        self.speakers_b = speakers_b

        # Volume in range 0..VOLUME_LEVELS. :class:`None` before calibration.
        self._nad_volume = None

        self._device = None

    def on_start(self):
        self._open_connection()
        self._set_device_to_known_state()

    def _open_connection(self):
        logger.info(u'NAD amplifier: Connecting through "%s"',
            self.port)
        self._device = serial.Serial(
            port=self.port,
            baudrate=self.BAUDRATE,
            bytesize=self.BYTESIZE,
            parity=self.PARITY,
            stopbits=self.STOPBITS,
            timeout=self.TIMEOUT)
        self._get_device_model()

    def _set_device_to_known_state(self):
        self._power_device_on()
        self._select_speakers()
        self._select_input_source()
        self.mute(False)
        self._calibrate_volume()

    def _get_device_model(self):
        model = self._ask_device('Main.Model')
        logger.info(u'NAD amplifier: Connected to model "%s"', model)
        return model

    def _power_device_on(self):
        self._check_and_set('Main.Power', 'On')

    def _select_speakers(self):
        if self.speakers_a is not None:
            self._check_and_set('Main.SpeakerA', self.speakers_a.title())
        if self.speakers_b is not None:
            self._check_and_set('Main.SpeakerB', self.speakers_b.title())

    def _select_input_source(self):
        if self.source is not None:
            self._check_and_set('Main.Source', self.source.title())

    def mute(self, mute):
        if mute:
            self._check_and_set('Main.Mute', 'On')
        else:
            self._check_and_set('Main.Mute', 'Off')

    def _calibrate_volume(self):
        # The NAD C 355BEE amplifier has 40 different volume levels. We have no
        # way of asking on which level we are. Thus, we must calibrate the
        # mixer by decreasing the volume 39 times.
        logger.info(u'NAD amplifier: Calibrating by setting volume to 0')
        self._nad_volume = self.VOLUME_LEVELS
        self.set_volume(0)
        logger.info(u'NAD amplifier: Done calibrating')

    def set_volume(self, volume):
        # Increase or decrease the amplifier volume until it matches the given
        # target volume.
        logger.debug(u'Setting volume to %d' % volume)
        target_nad_volume = int(round(volume * self.VOLUME_LEVELS / 100.0))
        if self._nad_volume is None:
            return  # Calibration needed
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

    def _check_and_set(self, key, value):
        for attempt in range(1, 4):
            if self._ask_device(key) == value:
                return
            logger.info(u'NAD amplifier: Setting "%s" to "%s" (attempt %d/3)',
                key, value, attempt)
            self._command_device(key, value)
        if self._ask_device(key) != value:
            logger.info(u'NAD amplifier: Gave up on setting "%s" to "%s"',
                key, value)

    def _ask_device(self, key):
        self._write('%s?' % key)
        return self._readline().replace('%s=' % key, '')

    def _command_device(self, key, value):
        if type(value) == unicode:
            value = value.encode('utf-8')
        self._write('%s=%s' % (key, value))
        self._readline()

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
