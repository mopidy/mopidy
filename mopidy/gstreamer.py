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


class GStreamer(ThreadingActor):
    """
    Audio output through `GStreamer <http://gstreamer.freedesktop.org/>`_.

    **Settings:**

    - :attr:`mopidy.settings.OUTPUTS`

    """

    def __init__(self):
        self._pipeline = None
        self._source = None
        self._taginject = None
        self._tee = None
        self._uridecodebin = None
        self._volume = None
        self._outputs = []
        self._handlers = {}

    def on_start(self):
        self._setup_gstreamer()

    def _setup_gstreamer(self):
        """
        **Warning:** :class:`GStreamer` requires
        :class:`mopidy.utils.process.GObjectEventThread` to be running. This is
        not enforced by :class:`GStreamer` itself.
        """
        description = ' ! '.join([
            'uridecodebin name=uri',
            'audioconvert name=convert',
            'volume name=volume',
            'taginject name=inject',
            'tee name=tee'])

        logger.debug(u'Setting up base GStreamer pipeline: %s', description)

        self._pipeline = gst.parse_launch(description)
        self._taginject = self._pipeline.get_by_name('inject')
        self._tee = self._pipeline.get_by_name('tee')
        self._volume = self._pipeline.get_by_name('volume')
        self._uridecodebin = self._pipeline.get_by_name('uri')

        self._uridecodebin.connect('notify::source', self._process_new_source)
        self._uridecodebin.connect('pad-added', self._process_new_pad,
            self._pipeline.get_by_name('convert').get_pad('sink'))

        for output in settings.OUTPUTS:
            get_class(output)(self).connect()

        # Setup bus and message processor
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._process_gstreamer_message)

    def _process_new_source(self, element, pad):
        self._source = element.get_by_name('source')
        try:
            self._source.set_property('caps', default_caps)
        except TypeError:
            pass

    def _process_new_pad(self, source, pad, target_pad):
        if not pad.is_linked():
            pad.link(target_pad)

    def _process_gstreamer_message(self, bus, message):
        """Process messages from GStreamer."""
        if message.src in self._handlers:
            if self._handlers[message.src](message):
                return # Message was handeled by output

        if message.type == gst.MESSAGE_EOS:
            logger.debug(u'GStreamer signalled end-of-stream. '
                'Telling backend ...')
            self._get_backend().playback.on_end_of_track()
        elif message.type == gst.MESSAGE_ERROR:
            error, debug = message.parse_error()
            logger.error(u'%s %s', error, debug)
            self.stop_playback()
        elif message.type == gst.MESSAGE_WARNING:
            error, debug = message.parse_warning()
            logger.warning(u'%s %s', error, debug)

    def _get_backend(self):
        backend_refs = ActorRegistry.get_by_class(Backend)
        assert len(backend_refs) == 1, 'Expected exactly one running backend.'
        return backend_refs[0].proxy()

    def set_uri(self, uri):
        """
        Change internal uridecodebin's URI

        :param uri: the URI to play
        :type uri: string
        """
        self._uridecodebin.set_property('uri', uri)

    def deliver_data(self, capabilities, data):
        """
        Deliver audio data to be played

        :param capabilities: a GStreamer capabilities string
        :type capabilities: string
        :param data: raw audio data to be played
        """
        caps = gst.caps_from_string(capabilities)
        buffer_ = gst.Buffer(buffer(data))
        buffer_.set_caps(caps)
        self._source.set_property('caps', caps)
        self._source.emit('push-buffer', buffer_)

    def end_of_data_stream(self):
        """
        Add end-of-stream token to source.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.
        """
        self._source.emit('end-of-stream')

    def get_position(self):
        """
        Get position in milliseconds.

        :rtype: int
        """
        if self._pipeline.get_state()[1] == gst.STATE_NULL:
            return 0
        try:
            position = self._pipeline.query_position(gst.FORMAT_TIME)[0]
            return position // gst.MSECOND
        except gst.QueryError, e:
            logger.error('time_position failed: %s', e)
            return 0

    def set_position(self, position):
        """
        Set position in milliseconds.

        :param position: the position in milliseconds
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self._pipeline.get_state() # block until state changes are done
        handeled = self._pipeline.seek_simple(gst.Format(gst.FORMAT_TIME),
            gst.SEEK_FLAG_FLUSH, position * gst.MSECOND)
        self._pipeline.get_state() # block until seek is done
        return handeled

    def start_playback(self):
        """Notify GStreamer that it should start playback"""
        return self._set_state(gst.STATE_PLAYING)

    def pause_playback(self):
        """Notify GStreamer that it should pause playback"""
        return self._set_state(gst.STATE_PAUSED)

    def prepare_change(self):
        """
        Notify GStreamer that we are about to change state of playback.

        This function always needs to be called before changing URIS or doing
        changes like updating data that is being pushed. The reason for this
        is that GStreamer will reset all its state when it changes to
        :attr:`gst.STATE_READY`.
        """
        return self._set_state(gst.STATE_READY)

    def stop_playback(self):
        """Notify GStreamer that is should stop playback"""
        return self._set_state(gst.STATE_NULL)

    def _set_state(self, state):
        """
        Set the GStreamer state. Returns :class:`True` if successful.

        .. digraph:: gst_state_transitions

            "NULL" -> "READY"
            "PAUSED" -> "PLAYING"
            "PAUSED" -> "READY"
            "PLAYING" -> "PAUSED"
            "READY" -> "NULL"
            "READY" -> "PAUSED"

        :param state: State to set pipeline to. One of: `gst.STATE_NULL`,
            `gst.STATE_READY`, `gst.STATE_PAUSED` and `gst.STATE_PLAYING`.
        :type state: :class:`gst.State`
        :rtype: :class:`True` or :class:`False`
        """
        result = self._pipeline.set_state(state)
        if result == gst.STATE_CHANGE_FAILURE:
            logger.warning('Setting GStreamer state to %s: failed',
                state.value_name)
            return False
        elif result == gst.STATE_CHANGE_ASYNC:
            logger.debug('Setting GStreamer state to %s: async',
                state.value_name)
            return True
        else:
            logger.debug('Setting GStreamer state to %s: OK',
                state.value_name)
            return True

    def get_volume(self):
        """
        Get volume level for software mixer.

        :rtype: int in range [0..100]
        """
        return int(self._volume.get_property('volume') * 100)

    def set_volume(self, volume):
        """
        Set volume level for software mixer.

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self._volume.set_property('volume', volume / 100.0)
        return True

    def set_metadata(self, track):
        """
        Set track metadata for currently playing song.

        Only needs to be called by sources such as appsrc which don't already
        inject tags in pipeline.

        :param track: Track containing metadata for current song.
        :type track: :class:`mopidy.modes.Track`
        """
        # FIXME what if we want to unset taginject tags?
        tags = u'artist="%(artist)s",title="%(title)s"' % {
            'artist': u', '.join([a.name for a in track.artists]),
            'title': track.name,
        }
        logger.debug('Setting tags to: %s', tags)
        self._taginject.set_property('tags', tags)

    def connect_output(self, output):
        """
        Connect output to pipeline.

        :param output: output to connect to our pipeline.
        :type output: :class:`gst.Bin`
        """
        self._pipeline.add(output)
        output.sync_state_with_parent() # Required to add to running pipe
        gst.element_link_many(self._tee, output)
        self._outputs.append(output)
        logger.info('Added %s', output.get_name())

    def list_outputs(self):
        return [output.get_name() for output in self._outputs]

    def remove_output(self, output):
        """
        Remove output from our pipeline.

        :param output: output to remove from our pipeline.
        :type output: :class:`gst.Bin`
        """
        if output not in self._outputs:
            raise LookupError('Ouput %s not present in pipeline'
                % output.get_name)
        teesrc = output.get_pad('sink').get_peer()
        handler = teesrc.add_event_probe(self._handle_event_probe)

        struct = gst.Structure('mopidy-unlink-tee')
        struct.set_value('handler', handler)

        event = gst.event_new_custom(gst.EVENT_CUSTOM_DOWNSTREAM, struct)
        self._tee.send_event(event)

    def _handle_event_probe(self, teesrc, event):
        if event.type == gst.EVENT_CUSTOM_DOWNSTREAM and event.has_name('mopidy-unlink-tee'):
            data = self._get_structure_data(event.get_structure())

            output = teesrc.get_peer().get_parent()

            teesrc.unlink(teesrc.get_peer())
            teesrc.remove_event_probe(data['handler'])

            output.set_state(gst.STATE_NULL)
            self._pipeline.remove(output)

            logger.warning('Removed %s', output.get_name())
            return False
        return True

    def _get_structure_data(self, struct):
        # Ugly hack to get around missing get_value in pygst bindings :/
        data = {}
        def get_data(key, value):
            data[key] = value
        struct.foreach(get_data)
        return data

    def connect_message_handler(self, element, handler):
        """
        Attach custom message handler for given element.

        Hook to allow outputs (or other code) to register custom message
        handlers for all messages coming from the element in question.

        In the case of outputs :meth:`mopidy.outputs.BaseOuptut.on_connect`
        should be used to attach such handlers and care should be taken to
        remove them in :meth:`mopidy.outputs.BaseOuptut.on_remove`.

        The handler callback will only be given the message in question, and
        is free to ignore the message. However, if the handler wants to prevent
        the default handling of the message it should return :class:`True`
        indicating that the message has been handled.

        (Note that there can only be on handler per element)

        :param element: element to watch messages from
        :type element: :class:`gst.Element`
        :param handler: function that expects `gst.Message`, should return
            ``True`` if message has been handeled.
        """
        self._handlers[element] = handler

    def remove_message_handler(self, element):
        """
        Remove custom message handler.

        :param element: element to remove message handling from.
        :type element: :class:`gst.Element`
        """
        self._handlers.pop(element, None)
