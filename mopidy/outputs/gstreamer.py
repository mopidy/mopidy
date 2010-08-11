import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst

import logging
import threading

from mopidy.process import BaseProcess, unpickle_connection

logger = logging.getLogger('mopidy.outputs.gstreamer')

class GStreamerOutput(object):
    """
    Audio output through GStreamer.

    Starts the :class:`GStreamerProcess`.
    """

    def __init__(self, core_queue, input_connection):
        process = GStreamerProcess(core_queue, input_connection)
        process.start()

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

    def __init__(self, core_queue, input_connection):
        super(GStreamerProcess, self).__init__()
        self.core_queue = core_queue
        self.input_connection = input_connection
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
            if self.input_connection.poll(None):
                message = self.input_connection.recv()
                self.process_mopidy_message(message)

    def setup(self):
        logger.debug(u'Setting up GStreamer pipeline')

        # Start a helper thread that can run the gobject.MainLoop
        messages_thread = GStreamerMessagesThread()
        messages_thread.daemon = True
        messages_thread.start()

        # A pipeline consisting of many elements
        self.gst_pipeline = gst.Pipeline("pipeline")

        # Setup bus and message processor
        self.gst_bus = self.gst_pipeline.get_bus()
        self.gst_bus.add_signal_watch()
        self.gst_bus_id = self.gst_bus.connect('message',
            self.process_gst_message)

        # Bin for playing audio URIs
        #self.gst_uri_src = gst.element_factory_make('uridecodebin', 'uri_src')
        #self.gst_pipeline.add(self.gst_uri_src)

        # Bin for playing audio data
        self.gst_data_src = gst.element_factory_make('appsrc', 'data_src')
        self.gst_pipeline.add(self.gst_data_src)

        # Volume filter
        self.gst_volume = gst.element_factory_make('volume', 'volume')
        self.gst_pipeline.add(self.gst_volume)

        # Audio output sink
        self.gst_sink = gst.element_factory_make('autoaudiosink', 'sink')
        self.gst_pipeline.add(self.gst_sink)

        # Add callback that will link uri_src output with volume filter input
        # when the output pad is ready.
        # See http://stackoverflow.com/questions/2993777 for details.
        def on_new_decoded_pad(dbin, pad, is_last):
            uri_src = pad.get_parent()
            pipeline = uri_src.get_parent()
            volume = pipeline.get_by_name('volume')
            uri_src.link(volume)
            logger.debug("Linked uri_src's new decoded pad to volume filter")
        # FIXME uridecodebin got no new-decoded-pad signal, but it's
        # subcomponent decodebin2 got that signal. Fixing this is postponed
        # till after data_src is up and running perfectly
        #self.gst_uri_src.connect('new-decoded-pad', on_new_decoded_pad)

        # Link data source output with volume filter input
        self.gst_data_src.link(self.gst_volume)

        # Link volume filter output to audio sink input
        self.gst_volume.link(self.gst_sink)

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
        self.gst_uri_src.set_property('uri', uri)
        self.set_state('PLAYING')
        # TODO Return status

    def deliver_data(self, caps_string, data):
        """Deliver audio data to be played"""
        caps = gst.caps_from_string(caps_string)
        buffer_ = gst.Buffer(buffer(data))
        buffer_.set_caps(caps)
        self.gst_data_src.set_property('caps', caps)
        self.gst_data_src.emit('push-buffer', buffer_)

    def end_of_data_stream(self):
        """
        Add end-of-stream token to source.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.
        """
        self.gst_data_src.emit('end-of-stream')

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
