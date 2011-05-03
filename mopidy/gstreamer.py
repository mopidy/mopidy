import pygst
pygst.require('0.10')
import gst

import logging

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy import settings
from mopidy.utils import get_class
from mopidy.backends.base import Backend

logger = logging.getLogger('mopidy.gstreamer')

default_caps = gst.Caps("""
    audio/x-raw-int,
    endianness=(int)1234,
    channels=(int)2,
    width=(int)16,
    depth=(int)16,
    signed=(boolean)true,
    rate=(int)44100""")

class BaseOutput(object):
    def connect_bin(self, pipeline, element_to_link_to):
        """
        Connect output bin to pipeline and given element.
        """
        description = 'queue ! %s' % self.describe_bin()
        logger.debug('Adding new output to tee: %s', description)

        output = self.parse_bin(description)
        self.modify_bin(output)

        pipeline.add(output)
        output.sync_state_with_parent()
        gst.element_link_many(element_to_link_to, output)

    def parse_bin(self, description):
        return gst.parse_bin_from_description(description, True)

    def modify_bin(self, output):
        """
        Modifies bin before it is installed if needed
        """
        pass

    def describe_bin(self):
        """
        Describe bin to be parsed.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def set_properties(self, element, properties):
        """
        Set properties on element if they have a value.
        """
        for key, value in properties.items():
            if value:
                element.set_property(key, value)


class GStreamer(ThreadingActor):
    """
    Audio output through `GStreamer <http://gstreamer.freedesktop.org/>`_.

    **Settings:**

    - :attr:`mopidy.settings.GSTREAMER_AUDIO_SINK`

    """

    def __init__(self):
        self.gst_pipeline = None

    def on_start(self):
        self._setup_gstreamer()

    def _setup_gstreamer(self):
        """
        **Warning:** :class:`GStreamerOutput` requires
        :class:`mopidy.utils.process.GObjectEventThread` to be running. This is
        not enforced by :class:`GStreamerOutput` itself.
        """
        base_pipeline = ' ! '.join([
            'audioconvert name=convert',
            'volume name=volume',
            'taginject name=tag',
            'tee name=tee',
        ])

        logger.debug(u'Setting up base GStreamer pipeline: %s', base_pipeline)

        self.gst_pipeline = gst.parse_launch(base_pipeline)

        self.gst_tee = self.gst_pipeline.get_by_name('tee')
        self.gst_convert = self.gst_pipeline.get_by_name('convert')
        self.gst_volume = self.gst_pipeline.get_by_name('volume')
        self.gst_taginject = self.gst_pipeline.get_by_name('tag')

        self.gst_uridecodebin = gst.element_factory_make('uridecodebin', 'uri')
        self.gst_uridecodebin.connect('notify::source', self._process_new_source)
        self.gst_uridecodebin.connect('pad-added', self._process_new_pad,
            self.gst_convert.get_pad('sink'))
        self.gst_pipeline.add(self.gst_uridecodebin)

        for output in settings.OUTPUTS:
            output_cls = get_class(output)()
            output_cls.connect_bin(self.gst_pipeline, self.gst_tee)

        # Setup bus and message processor
        gst_bus = self.gst_pipeline.get_bus()
        gst_bus.add_signal_watch()
        gst_bus.connect('message', self._process_gstreamer_message)

    def _process_new_source(self, element, pad):
        source = element.get_by_name('source')
        try:
            source.set_property('caps', default_caps)
        except TypeError:
            pass

    def _process_new_pad(self, source, pad, target_pad):
        pad.link(target_pad)

    def _process_gstreamer_message(self, bus, message):
        """Process messages from GStreamer."""
        if message.type == gst.MESSAGE_EOS:
            logger.debug(u'GStreamer signalled end-of-stream. '
                'Telling backend ...')
            self._get_backend().playback.on_end_of_track()
        elif message.type == gst.MESSAGE_ERROR:
            self.stop_playback()
            error, debug = message.parse_error()
            logger.error(u'%s %s', error, debug)
            # FIXME Should we send 'stop_playback' to the backend here? Can we
            # differentiate on how serious the error is?

    def _get_backend(self):
        backend_refs = ActorRegistry.get_by_class(Backend)
        assert len(backend_refs) == 1, 'Expected exactly one running backend.'
        return backend_refs[0].proxy()

    def set_uri(self, uri):
        """Play audio at URI"""
        self.gst_uridecodebin.set_property('uri', uri)

    def deliver_data(self, caps_string, data):
        """Deliver audio data to be played"""
        source = self.gst_pipeline.get_by_name('source')
        caps = gst.caps_from_string(caps_string)
        buffer_ = gst.Buffer(buffer(data))
        buffer_.set_caps(caps)
        source.set_property('caps', caps)
        source.emit('push-buffer', buffer_)

    def end_of_data_stream(self):
        """
        Add end-of-stream token to source.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.
        """
        self.gst_pipeline.get_by_name('source').emit('end-of-stream')

    def get_position(self):
        if self.gst_pipeline.get_state()[1] == gst.STATE_NULL:
            return 0
        try:
            position = self.gst_pipeline.query_position(gst.FORMAT_TIME)[0]
            return position // gst.MSECOND
        except gst.QueryError, e:
            logger.error('time_position failed: %s', e)
            return 0

    def set_position(self, position):
        self.gst_pipeline.get_state() # block until state changes are done
        handeled = self.gst_pipeline.seek_simple(gst.Format(gst.FORMAT_TIME),
            gst.SEEK_FLAG_FLUSH, position * gst.MSECOND)
        self.gst_pipeline.get_state() # block until seek is done
        return handeled

    def start_playback(self):
        return self.set_state(gst.STATE_PLAYING)

    def pause_playback(self):
        return self.set_state(gst.STATE_PAUSE)

    def prepare_playback(self):
        return self.set_state(gst.STATE_READY)

    def stop_playback(self):
        return self.set_state(gst.STATE_NULL)

    def set_state(self, state):
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
        result = self.gst_pipeline.set_state(state)
        if result == gst.STATE_CHANGE_FAILURE:
            logger.warning('Setting GStreamer state to %s: failed',
                state.value_name)
            return False
        else:
            logger.debug('Setting GStreamer state to %s: OK',
                state.value_name)
            return True

    def get_volume(self):
        """Get volume in range [0..100]"""
        return int(self.gst_volume.get_property('volume') * 100)

    def set_volume(self, volume):
        """Set volume in range [0..100]"""
        self.gst_volume.set_property('volume', volume / 100.0)
        return True

    def set_metadata(self, track):
        tags = u'artist="%(artist)s",title="%(title)s"' % {
            'artist': u', '.join([a.name for a in track.artists]),
            'title': track.name,
        }
        logger.debug('Setting tags to: %s', tags)
        self.gst_taginject.set_property('tags', tags)
