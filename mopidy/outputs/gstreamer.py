import gobject

import pygst
pygst.require('0.10')

import gst
import logging

from mopidy.process import BaseProcess

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

    The main loop polls for events from both Mopidy and GStreamer.
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

    def _run(self):
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
        """Processes messages from the rest of Mopidy."""
        pass # TODO

    def process_gst_message(self, bus, message):
        """Processes message from GStreamer."""
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
        self.state_ready()
        self.gst_uri_src.set_property('uri', uri)
        self.state_playing()
        # TODO Return status

    def state_playing(self):
        """
        Set the state to PLAYING.

        Previous state should be READY or PAUSED.
        """
        result = self.gst_uri_src.set_state(gst.STATE_PLAYING)
        if result == gst.STATE_CHANGE_SUCCESS:
            logger.debug('Setting GStreamer state to PLAYING: OK')
            return True
        else:
            logger.warning('Setting GStreamer state to PLAYING: failed')
            return False

    def state_paused(self):
        """
        Set the state to PAUSED.

        Previous state should be PLAYING.
        """
        result = self.gst_uri_src.set_state(gst.STATE_PAUSED)
        if result == gst.STATE_CHANGE_SUCCESS:
            logger.debug('Setting GStreamer state to PAUSED: OK')
            return True
        else:
            logger.warning('Setting GStreamer state to PAUSED: failed')
            return False

    def state_ready(self):
        """
        Set the state to READY.
        """
        result = self.gst_uri_src.set_state(gst.STATE_READY)
        if result == gst.STATE_CHANGE_SUCCESS:
            logger.debug('Setting GStreamer state to READY: OK')
            return True
        else:
            logger.warning('Setting GStreamer state to READY: failed')
            return False

    def get_volume(self):
        """Get volume in range [0..100]"""
        gst_volume = self.gst_volume.get_property('volume')
        return int(gst_volume * 100)

    def set_volume(self, volume):
        """Set volume in range [0..100]"""
        gst_volume = volume / 100.0
        self.gst_volume.set_property('volume', gst_volume)
