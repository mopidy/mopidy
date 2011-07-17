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

    - :attr:`mopidy.settings.OUTPUT`

    """

    def __init__(self):
        self._pipeline = None
        self._source = None
        self._uridecodebin = None
        self._volume = None
        self._outputs = []
        self._handlers = {}

    def on_start(self):
        # **Warning:** :class:`GStreamer` requires
        # :class:`mopidy.utils.process.GObjectEventThread` to be running. This
        # is not enforced by :class:`GStreamer` itself.
        self._setup_pipeline()
        self._setup_outputs()
        self._setup_message_processor()

    def _setup_pipeline(self):
        description = ' ! '.join([
            'uridecodebin name=uri',
            'audioconvert name=convert',
            'volume name=volume'])

        logger.debug(u'Setting up base GStreamer pipeline: %s', description)

        self._pipeline = gst.parse_launch(description)
        self._volume = self._pipeline.get_by_name('volume')
        self._uridecodebin = self._pipeline.get_by_name('uri')

        self._uridecodebin.connect('notify::source', self._on_new_source)
        self._uridecodebin.connect('pad-added', self._on_new_pad,
            self._pipeline.get_by_name('convert').get_pad('sink'))

    def _setup_outputs(self):
        for klass in settings.OUTPUTS:
            self._outputs.append(get_class(klass)())
        self.connect_output(self._outputs[0].bin)

    def _setup_message_processor(self):
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_message)

    def _on_new_source(self, element, pad):
        self._source = element.get_property('source')
        try:
            self._source.set_property('caps', default_caps)
        except TypeError:
            pass

    def _on_new_pad(self, source, pad, target_pad):
        if not pad.is_linked():
            pad.link(target_pad)

    def _on_message(self, bus, message):
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
        Set URI of audio to be played.

        You *MUST* call :meth:`prepare_change` before calling this method.

        :param uri: the URI to play
        :type uri: string
        """
        self._uridecodebin.set_property('uri', uri)

    def emit_data(self, capabilities, data):
        """
        Call this to deliver raw audio data to be played.

        :param capabilities: a GStreamer capabilities string
        :type capabilities: string
        :param data: raw audio data to be played
        """
        caps = gst.caps_from_string(capabilities)
        buffer_ = gst.Buffer(buffer(data))
        buffer_.set_caps(caps)
        self._source.set_property('caps', caps)
        self._source.emit('push-buffer', buffer_)

    def emit_end_of_stream(self):
        """
        Put an end-of-stream token on the pipeline. This is typically used in
        combination with :meth:`emit_data`.

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
        """
        Notify GStreamer that it should start playback.

        :rtype: :class:`True` if successfull, else :class:`False`
        """
        return self._set_state(gst.STATE_PLAYING)

    def pause_playback(self):
        """
        Notify GStreamer that it should pause playback.

        :rtype: :class:`True` if successfull, else :class:`False`
        """
        return self._set_state(gst.STATE_PAUSED)

    def prepare_change(self):
        """
        Notify GStreamer that we are about to change state of playback.

        This function *MUST* be called before changing URIs or doing
        changes like updating data that is being pushed. The reason for this
        is that GStreamer will reset all its state when it changes to
        :attr:`gst.STATE_READY`.
        """
        return self._set_state(gst.STATE_READY)

    def stop_playback(self):
        """
        Notify GStreamer that is should stop playback.

        :rtype: :class:`True` if successfull, else :class:`False`
        """
        return self._set_state(gst.STATE_NULL)

    def _set_state(self, state):
        """
        Internal method for setting the raw GStreamer state.

        .. digraph:: gst_state_transitions

            graph [rankdir="LR"];
            node [fontsize=10];

            "NULL" -> "READY"
            "PAUSED" -> "PLAYING"
            "PAUSED" -> "READY"
            "PLAYING" -> "PAUSED"
            "READY" -> "NULL"
            "READY" -> "PAUSED"

        :param state: State to set pipeline to. One of: `gst.STATE_NULL`,
            `gst.STATE_READY`, `gst.STATE_PAUSED` and `gst.STATE_PLAYING`.
        :type state: :class:`gst.State`
        :rtype: :class:`True` if successfull, else :class:`False`
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
        Get volume level of the GStreamer software mixer.

        :rtype: int in range [0..100]
        """
        return int(self._volume.get_property('volume') * 100)

    def set_volume(self, volume):
        """
        Set volume level of the GStreamer software mixer.

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self._volume.set_property('volume', volume / 100.0)
        return True

    def set_metadata(self, track):
        """
        Set track metadata for currently playing song.

        Only needs to be called by sources such as `appsrc` which do not
        already inject tags in pipeline, e.g. when using :meth:`emit_data` to
        deliver raw audio data to GStreamer.

        :param track: the current track
        :type track: :class:`mopidy.modes.Track`
        """
        taglist = gst.TagList()
        artists = [a for a in (track.artists or []) if a.name]

        # Default to blank data to trick shoutcast into clearing any previous
        # values it might have.
        taglist[gst.TAG_ARTIST] = u' '
        taglist[gst.TAG_TITLE] = u' '
        taglist[gst.TAG_ALBUM] = u' '

        if artists:
            taglist[gst.TAG_ARTIST] = u', '.join([a.name for a in artists])

        if track.name:
            taglist[gst.TAG_TITLE] = track.name

        if track.album and track.album.name:
            taglist[gst.TAG_ALBUM] = track.album.name

        event = gst.event_new_tag(taglist)
        self._pipeline.send_event(event)

    def connect_output(self, output):
        """
        Connect output to pipeline.

        :param output: output to connect to the pipeline
        :type output: :class:`gst.Bin`
        """
        self._pipeline.add(output)
        output.sync_state_with_parent() # Required to add to running pipe
        gst.element_link_many(self._volume, output)
        logger.debug('Output set to %s', output.get_name())

    # FIXME re-add disconnect / swap output code?
