import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst

import logging
import threading

from mopidy import settings
from mopidy.process import BaseProcess, unpickle_connection

logger = logging.getLogger('mopidy.outputs.gstreamer')

class GStreamerOutput(object):
    """
    Audio output through GStreamer.

    Starts the :class:`GStreamerProcess`.
    """

    def __init__(self, core_queue, output_queue):
        self.process = GStreamerProcess(core_queue, output_queue)
        self.process.start()

    def destroy(self):
        self.process.terminate()

class GStreamerMessagesThread(threading.Thread):
    def run(self):
        gobject.MainLoop().run()

class GStreamerProcess(BaseProcess):
    """
    A process for all work related to GStreamer.

    The main loop processes events from both Mopidy and GStreamer.

    Make sure this subprocess is started by the MainThread in the top-most
    parent process, and not some other thread. If not, we can get into the
    problems described at
    http://jameswestby.net/weblog/tech/14-caution-python-multiprocessing-and-glib-dont-mix.html.
    """

    def __init__(self, core_queue, output_queue):
        super(GStreamerProcess, self).__init__()
        self.core_queue = core_queue
        self.output_queue = output_queue
        self.gst_pipeline = None

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.output_queue.get()
            self.process_mopidy_message(message)

    def setup(self):
        logger.debug(u'Setting up GStreamer pipeline')

        # Start a helper thread that can run the gobject.MainLoop
        messages_thread = GStreamerMessagesThread()
        messages_thread.daemon = True
        messages_thread.start()

        self.gst_pipeline = gst.parse_launch(' ! '.join([
            'audioconvert name=convert',
            'volume name=volume',
            'autoaudiosink'
        ]))

        pad = self.gst_pipeline.get_by_name('convert').get_pad('sink')

        if settings.BACKENDS[0] == 'mopidy.backends.local.LocalBackend':
            uri_bin = gst.element_factory_make('uridecodebin', 'uri')
            uri_bin.connect('pad-added', self.process_new_pad, pad)
            self.gst_pipeline.add(uri_bin)
        else:
            app_src = gst.element_factory_make('appsrc', 'src')
            self.gst_pipeline.add(app_src)
            app_src.get_pad('src').link(pad)

        # Setup bus and message processor
        gst_bus = self.gst_pipeline.get_bus()
        gst_bus.add_signal_watch()
        gst_bus.connect('message', self.process_gst_message)

    def process_new_pad(self, source, pad, target_pad):
        pad.link(target_pad)

    def process_mopidy_message(self, message):
        """Process messages from the rest of Mopidy."""
        if message['command'] == 'play_uri':
            response = self.play_uri(message['uri'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'deliver_data':
            self.deliver_data(message['caps'], message['data'])
        elif message['command'] == 'end_of_data_stream':
            self.end_of_data_stream()
        elif message['command'] == 'set_state':
            response = self.set_state(message['state'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'get_volume':
            volume = self.get_volume()
            connection = unpickle_connection(message['reply_to'])
            connection.send(volume)
        elif message['command'] == 'set_volume':
            self.set_volume(message['volume'])
        elif message['command'] == 'set_position':
            self.set_position(message['position'])
        elif message['command'] == 'get_position':
            response = self.get_position()
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        else:
            logger.warning(u'Cannot handle message: %s', message)

    def process_gst_message(self, bus, message):
        """Process messages from GStreamer."""
        if message.type == gst.MESSAGE_EOS:
            logger.debug(u'GStreamer signalled end-of-stream. '
                'Sending end_of_track to core_queue ...')
            self.core_queue.put({'command': 'end_of_track'})
        elif message.type == gst.MESSAGE_ERROR:
            self.set_state('NULL')
            error, debug = message.parse_error()
            logger.error(u'%s %s', error, debug)
            # FIXME Should we send 'stop_playback' to core here? Can we
            # differentiate on how serious the error is?

    def play_uri(self, uri):
        """Play audio at URI"""
        self.set_state('READY')
        self.gst_pipeline.get_by_name('uri').set_property('uri', uri)
        return self.set_state('PLAYING')

    def deliver_data(self, caps_string, data):
        """Deliver audio data to be played"""
        data_src = self.gst_pipeline.get_by_name('src')
        caps = gst.caps_from_string(caps_string)
        buffer_ = gst.Buffer(buffer(data))
        buffer_.set_caps(caps)
        data_src.set_property('caps', caps)
        data_src.emit('push-buffer', buffer_)

    def end_of_data_stream(self):
        """
        Add end-of-stream token to source.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.
        """
        self.gst_pipeline.get_by_name('src').emit('end-of-stream')

    def set_state(self, state_name):
        """
        Set the GStreamer state. Returns :class:`True` if successful.

        .. digraph:: gst_state_transitions

            "NULL" -> "READY"
            "PAUSED" -> "PLAYING"
            "PAUSED" -> "READY"
            "PLAYING" -> "PAUSED"
            "READY" -> "NULL"
            "READY" -> "PAUSED"

        :param state_name: NULL, READY, PAUSED, or PLAYING
        :type state_name: string
        :rtype: :class:`True` or :class:`False`
        """
        result = self.gst_pipeline.set_state(
            getattr(gst, 'STATE_' + state_name))
        if result == gst.STATE_CHANGE_FAILURE:
            logger.warning('Setting GStreamer state to %s: failed', state_name)
            return False
        else:
            logger.debug('Setting GStreamer state to %s: OK', state_name)
            return True

    def get_volume(self):
        """Get volume in range [0..100]"""
        gst_volume = self.gst_pipeline.get_by_name('volume')
        return int(gst_volume.get_property('volume') * 100)

    def set_volume(self, volume):
        """Set volume in range [0..100]"""
        gst_volume = self.gst_pipeline.get_by_name('volume')
        gst_volume.set_property('volume', volume / 100.0)

    def set_position(self, position):
        self.gst_pipeline.seek_simple(gst.Format(gst.FORMAT_TIME),
            gst.SEEK_FLAG_FLUSH, position * gst.MSECOND)
        self.gst_pipeline.get_state()

    def get_position(self):
        try:
            position = self.gst_pipeline.query_position(gst.FORMAT_TIME)[0]
            return position // gst.MSECOND
        except gst.QueryError, e:
            logger.error('time_position failed: %s', e)
            return 0
