import gobject

import pygst
pygst.require('0.10')

import gst
import logging

from mopidy.process import BaseProcess, unpickle_connection

logger = logging.getLogger('mopidy.outputs.gstreamer')

class GStreamerOutput(object):
    """
    Audio output through GStreamer.

    Starts the :class:`GStreamerProcess`.
    """

    def __init__(self, core_queue):
        process = GStreamerProcess(core_queue)
        process.start()

class GStreamerProcess(BaseProcess):
    """
    A process for all work related to GStreamer.

    The main loop processes events from both Mopidy and GStreamer.
    """

    def __init__(self, core_queue):
        super(GStreamerProcess, self).__init__()
        self.core_queue = core_queue
        self.gobject_context = None
        self.gst_pipeline = None
        self.gst_bus = None
        self.gst_bus_id = None
        self.gst_uri_src = None
        self.gst_data_src = None
        self.gst_volume = None
        self.gst_sink = None

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.core_queue.get()
            self.process_core_message(message)
            self.gobject_context.iteration(True)

    def setup(self):
        # See http://www.jejik.com/articles/2007/01/
        # python-gstreamer_threading_and_the_main_loop/ for details.
        gobject.threads_init()
        self.gobject_context = gobject.MainLoop().get_context()

        # A pipeline consisting of many elements
        self.gst_pipeline = gst.Pipeline("pipeline")

        # Setup bus and message processor
        self.gst_bus = self.gst_pipeline.get_bus()
        self.gst_bus.add_signal_watch()
        self.gst_bus_id = self.gst_bus.connect('message',
            self.process_gst_message)

        # Bin for playing audio URIs
        self.gst_uri_src = gst.element_factory_make('uridecodebin', 'uri_src')
        self.gst_pipeline.add(self.gst_uri_src)

        # Bin for playing audio data
        self.gst_data_src = gst.element_factory_make('appsrc', 'data_src')
        self.gst_pipeline.add(self.gst_data_src)

        # Volume filter
        self.gst_volume = gst.element_factory_make('volume', 'volume')
        self.gst_pipeline.add(self.gst_volume)

        # Audio output sink
        self.gst_sink = gst.element_factory_make('autoaudiosink', 'sink')
        self.gst_pipeline.add(self.gst_sink)

        # The audio URI chain
        gst.element_link_many(self.gst_uri_src, self.gst_volume, self.gst_sink)

        # The audio data chain
        gst.element_link_many(self.gst_data_src, self.gst_volume,
            self.gst_sink)

    def process_core_message(self, message):
        """Process messages from the rest of Mopidy."""
        assert message['to'] == 'gstreamer', 'Message must be addressed to us'
        if message['command'] == 'play_uri':
            response = self.play_uri(message['uri'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'deliver_data':
            # TODO Do we care about sending responses for every data delivery?
            self.deliver_data(message['caps'], message['data'])
        elif message['command'] == 'set_state':
            response = self.set_state(message['state'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        else:
            logger.warning(u'Cannot handle message: %s', message)

    def process_gst_message(self, bus, message):
        """Process messages from GStreamer."""
        if message.type == gst.MESSAGE_EOS:
            pass # TODO Handle end of track/stream
        elif message.type == gst.MESSAGE_ERROR:
            self.gst_bin.set_state(gst.STATE_NULL)
            error, debug = message.parse_error()
            logger.error(u'%s %s', error, debug)

    def deliver_data(self, caps_string, data):
        """Deliver audio data to be played"""
        caps = gst.caps_from_string(caps_string)
        buffer_ = gst.Buffer(data)
        buffer_.set_caps(caps)
        self.gst_data_src.emit('push-buffer', buffer_)

    def play_uri(self, uri):
        """Play audio at URI"""
        self.set_state('READY')
        self.gst_uri_src.set_property('uri', uri)
        self.set_state('PLAYING')
        # TODO Return status

    def set_state(self, state_name):
        """
        Set the GStreamer state. Returns :class:`True` if successful.

        :param state_name: READY, PLAYING, or PAUSED
        :type state_name: string
        :rtype: :class:`True` or :class:`False`
        """
        result = self.gst_uri_src.set_state(
            getattr(gst, 'STATE_' + state_name))
        if result == gst.STATE_CHANGE_SUCCESS:
            logger.debug('Setting GStreamer state to %s: OK', state_name)
            return True
        else:
            logger.warning('Setting GStreamer state to %s: failed', state_name)
            return False

    def get_volume(self):
        """Get volume in range [0..100]"""
        gst_volume = self.gst_volume.get_property('volume')
        return int(gst_volume * 100)

    def set_volume(self, volume):
        """Set volume in range [0..100]"""
        gst_volume = volume / 100.0
        self.gst_volume.set_property('volume', gst_volume)
