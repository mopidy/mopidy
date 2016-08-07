from __future__ import absolute_import, unicode_literals

import logging
import os
import threading

import pykka

from mopidy import exceptions
from mopidy.audio import tags as tags_lib, utils
from mopidy.audio.constants import PlaybackState
from mopidy.audio.listener import AudioListener
from mopidy.internal import deprecation, process
from mopidy.internal.gi import GObject, Gst, GstPbutils


logger = logging.getLogger(__name__)

# This logger is only meant for debug logging of low level GStreamer info such
# as callbacks, event, messages and direct interaction with GStreamer such as
# set_state() on a pipeline.
gst_logger = logging.getLogger('mopidy.audio.gst')

_GST_PLAY_FLAGS_AUDIO = 0x02

_GST_STATE_MAPPING = {
    Gst.State.PLAYING: PlaybackState.PLAYING,
    Gst.State.PAUSED: PlaybackState.PAUSED,
    Gst.State.NULL: PlaybackState.STOPPED,
}


# TODO: expose this as a property on audio?
class _Appsrc(object):

    """Helper class for dealing with appsrc based playback."""

    def __init__(self):
        self._signals = utils.Signals()
        self.reset()

    def reset(self):
        """Reset the helper.

        Should be called whenever the source changes and we are not setting up
        a new appsrc.
        """
        self.prepare(None, None, None, None)

    def prepare(self, caps, need_data, enough_data, seek_data):
        """Store info we will need when the appsrc element gets installed."""
        self._signals.clear()
        self._source = None
        self._caps = caps
        self._need_data_callback = need_data
        self._seek_data_callback = seek_data
        self._enough_data_callback = enough_data

    def configure(self, source):
        """Configure the supplied source for use.

        Should be called whenever we get a new appsrc.
        """
        source.set_property('caps', self._caps)
        source.set_property('format', b'time')
        source.set_property('stream-type', b'seekable')
        source.set_property('max-bytes', 1 << 20)  # 1MB
        source.set_property('min-percent', 50)

        if self._need_data_callback:
            self._signals.connect(source, 'need-data', self._on_signal,
                                  self._need_data_callback)
        if self._seek_data_callback:
            self._signals.connect(source, 'seek-data', self._on_signal,
                                  self._seek_data_callback)
        if self._enough_data_callback:
            self._signals.connect(source, 'enough-data', self._on_signal, None,
                                  self._enough_data_callback)

        self._source = source

    def push(self, buffer_):
        if self._source is None:
            return False

        if buffer_ is None:
            gst_logger.debug('Sending appsrc end-of-stream event.')
            result = self._source.emit('end-of-stream')
            return result == Gst.FlowReturn.OK
        else:
            result = self._source.emit('push-buffer', buffer_)
            return result == Gst.FlowReturn.OK

    def _on_signal(self, element, clocktime, func):
        # This shim is used to ensure we always return true, and also handles
        # that not all the callbacks have a time argument.
        if clocktime is None:
            func()
        else:
            func(utils.clocktime_to_millisecond(clocktime))
        return True


# TODO: expose this as a property on audio when #790 gets further along.
class _Outputs(Gst.Bin):

    def __init__(self):
        Gst.Bin.__init__(self)
        # TODO gst1: Set 'outputs' as the Bin name for easier debugging

        self._tee = Gst.ElementFactory.make('tee')
        self.add(self._tee)

        ghost_pad = Gst.GhostPad.new('sink', self._tee.get_static_pad('sink'))
        self.add_pad(ghost_pad)

        # Add an always connected fakesink which respects the clock so the tee
        # doesn't fail even if we don't have any outputs.
        fakesink = Gst.ElementFactory.make('fakesink')
        fakesink.set_property('sync', True)
        self._add(fakesink)

    def add_output(self, description):
        # XXX This only works for pipelines not in use until #790 gets done.
        try:
            output = Gst.parse_bin_from_description(
                description, ghost_unlinked_pads=True)
        except GObject.GError as ex:
            logger.error(
                'Failed to create audio output "%s": %s', description, ex)
            raise exceptions.AudioException(bytes(ex))

        self._add(output)
        logger.info('Audio output set to "%s"', description)

    def _add(self, element):
        queue = Gst.ElementFactory.make('queue')
        self.add(element)
        self.add(queue)
        queue.link(element)
        self._tee.link(queue)


class SoftwareMixer(object):
    pykka_traversable = True

    def __init__(self, mixer):
        self._mixer = mixer
        self._element = None
        self._last_volume = None
        self._last_mute = None
        self._signals = utils.Signals()

    def setup(self, element, mixer_ref):
        self._element = element
        self._mixer.setup(mixer_ref)

    def teardown(self):
        self._signals.clear()
        self._mixer.teardown()

    def get_volume(self):
        return int(round(self._element.get_property('volume') * 100))

    def set_volume(self, volume):
        self._element.set_property('volume', volume / 100.0)
        self._mixer.trigger_volume_changed(self.get_volume())

    def get_mute(self):
        return self._element.get_property('mute')

    def set_mute(self, mute):
        self._element.set_property('mute', bool(mute))
        self._mixer.trigger_mute_changed(self.get_mute())


class _Handler(object):

    def __init__(self, audio):
        self._audio = audio
        self._element = None
        self._pad = None
        self._message_handler_id = None
        self._event_handler_id = None

    def setup_message_handling(self, element):
        self._element = element
        bus = element.get_bus()
        bus.add_signal_watch()
        self._message_handler_id = bus.connect('message', self.on_message)

    def setup_event_handling(self, pad):
        self._pad = pad
        self._event_handler_id = pad.add_probe(
            Gst.PadProbeType.EVENT_BOTH, self.on_pad_event)

    def teardown_message_handling(self):
        bus = self._element.get_bus()
        bus.remove_signal_watch()
        bus.disconnect(self._message_handler_id)
        self._message_handler_id = None

    def teardown_event_handling(self):
        self._pad.remove_probe(self._event_handler_id)
        self._event_handler_id = None

    def on_message(self, bus, msg):
        if msg.type == Gst.MessageType.STATE_CHANGED:
            if msg.src != self._element:
                return
            old_state, new_state, pending_state = msg.parse_state_changed()
            self.on_playbin_state_changed(old_state, new_state, pending_state)
        elif msg.type == Gst.MessageType.BUFFERING:
            self.on_buffering(msg.parse_buffering(), msg.get_structure())
        elif msg.type == Gst.MessageType.EOS:
            self.on_end_of_stream()
        elif msg.type == Gst.MessageType.ERROR:
            error, debug = msg.parse_error()
            self.on_error(error, debug)
        elif msg.type == Gst.MessageType.WARNING:
            error, debug = msg.parse_warning()
            self.on_warning(error, debug)
        elif msg.type == Gst.MessageType.ASYNC_DONE:
            self.on_async_done()
        elif msg.type == Gst.MessageType.TAG:
            taglist = msg.parse_tag()
            self.on_tag(taglist)
        elif msg.type == Gst.MessageType.ELEMENT:
            if GstPbutils.is_missing_plugin_message(msg):
                self.on_missing_plugin(msg)
        elif msg.type == Gst.MessageType.STREAM_START:
            self.on_stream_start()

    def on_pad_event(self, pad, pad_probe_info):
        event = pad_probe_info.get_event()
        if event.type == Gst.EventType.SEGMENT:
            self.on_segment(event.parse_segment())
        return Gst.PadProbeReturn.OK

    def on_playbin_state_changed(self, old_state, new_state, pending_state):
        gst_logger.debug(
            'Got STATE_CHANGED bus message: old=%s new=%s pending=%s',
            old_state.value_name, new_state.value_name,
            pending_state.value_name)

        if new_state == Gst.State.READY and pending_state == Gst.State.NULL:
            # XXX: We're not called on the last state change when going down to
            # NULL, so we rewrite the second to last call to get the expected
            # behavior.
            new_state = Gst.State.NULL
            pending_state = Gst.State.VOID_PENDING

        if pending_state != Gst.State.VOID_PENDING:
            return  # Ignore intermediate state changes

        if new_state == Gst.State.READY:
            return  # Ignore READY state as it's GStreamer specific

        new_state = _GST_STATE_MAPPING[new_state]
        old_state, self._audio.state = self._audio.state, new_state

        target_state = _GST_STATE_MAPPING.get(self._audio._target_state)
        if target_state is None:
            # XXX: Workaround for #1430, to be fixed properly by #1222.
            logger.debug('Race condition happened. See #1222 and #1430.')
            return
        if target_state == new_state:
            target_state = None

        logger.debug('Audio event: state_changed(old_state=%s, new_state=%s, '
                     'target_state=%s)', old_state, new_state, target_state)
        AudioListener.send('state_changed', old_state=old_state,
                           new_state=new_state, target_state=target_state)
        if new_state == PlaybackState.STOPPED:
            logger.debug('Audio event: stream_changed(uri=None)')
            AudioListener.send('stream_changed', uri=None)

        if 'GST_DEBUG_DUMP_DOT_DIR' in os.environ:
            Gst.debug_bin_to_dot_file(
                self._audio._playbin, Gst.DebugGraphDetails.ALL, 'mopidy')

    def on_buffering(self, percent, structure=None):
        if structure is not None and structure.has_field('buffering-mode'):
            buffering_mode = structure.get_enum(
                'buffering-mode', Gst.BufferingMode)
            if buffering_mode == Gst.BufferingMode.LIVE:
                return  # Live sources stall in paused.

        level = logging.getLevelName('TRACE')
        if percent < 10 and not self._audio._buffering:
            self._audio._playbin.set_state(Gst.State.PAUSED)
            self._audio._buffering = True
            level = logging.DEBUG
        if percent == 100:
            self._audio._buffering = False
            if self._audio._target_state == Gst.State.PLAYING:
                self._audio._playbin.set_state(Gst.State.PLAYING)
            level = logging.DEBUG

        gst_logger.log(
            level, 'Got BUFFERING bus message: percent=%d%%', percent)

    def on_end_of_stream(self):
        gst_logger.debug('Got EOS (end of stream) bus message.')
        logger.debug('Audio event: reached_end_of_stream()')
        self._audio._tags = {}
        AudioListener.send('reached_end_of_stream')

    def on_error(self, error, debug):
        error_msg = str(error).decode('utf-8')
        debug_msg = debug.decode('utf-8')
        gst_logger.debug(
            'Got ERROR bus message: error=%r debug=%r', error_msg, debug_msg)
        gst_logger.error('GStreamer error: %s', error_msg)
        # TODO: is this needed?
        self._audio.stop_playback()

    def on_warning(self, error, debug):
        error_msg = str(error).decode('utf-8')
        debug_msg = debug.decode('utf-8')
        gst_logger.warning('GStreamer warning: %s', error_msg)
        gst_logger.debug(
            'Got WARNING bus message: error=%r debug=%r', error_msg, debug_msg)

    def on_async_done(self):
        gst_logger.debug('Got ASYNC_DONE bus message.')

    def on_tag(self, taglist):
        tags = tags_lib.convert_taglist(taglist)
        gst_logger.debug('Got TAG bus message: tags=%r', dict(tags))

        # Postpone emitting tags until stream start.
        if self._audio._pending_tags is not None:
            self._audio._pending_tags.update(tags)
            return

        # TODO: Add proper tests for only emitting changed tags.
        unique = object()
        changed = []
        for key, value in tags.items():
            # Update any tags that changed, and store changed keys.
            if self._audio._tags.get(key, unique) != value:
                self._audio._tags[key] = value
                changed.append(key)

        if changed:
            logger.debug('Audio event: tags_changed(tags=%r)', changed)
            AudioListener.send('tags_changed', tags=changed)

    def on_missing_plugin(self, msg):
        desc = GstPbutils.missing_plugin_message_get_description(msg)
        debug = GstPbutils.missing_plugin_message_get_installer_detail(msg)
        gst_logger.debug(
            'Got missing-plugin bus message: description=%r', desc)
        logger.warning('Could not find a %s to handle media.', desc)
        if GstPbutils.install_plugins_supported():
            logger.info('You might be able to fix this by running: '
                        'gst-installer "%s"', debug)
        # TODO: store the missing plugins installer info in a file so we can
        # can provide a 'mopidy install-missing-plugins' if the system has the
        # required helper installed?

    def on_stream_start(self):
        gst_logger.debug('Got STREAM_START bus message')
        uri = self._audio._pending_uri
        logger.debug('Audio event: stream_changed(uri=%r)', uri)
        AudioListener.send('stream_changed', uri=uri)

        # Emit any postponed tags that we got after about-to-finish.
        tags, self._audio._pending_tags = self._audio._pending_tags, None
        self._audio._tags = tags or {}

        if tags:
            logger.debug('Audio event: tags_changed(tags=%r)', tags.keys())
            AudioListener.send('tags_changed', tags=tags.keys())

        if self._audio._pending_metadata:
            self._audio._playbin.send_event(self._audio._pending_metadata)
            self._audio._pending_metadata = None

    def on_segment(self, segment):
        gst_logger.debug(
            'Got SEGMENT pad event: '
            'rate=%(rate)s format=%(format)s start=%(start)s stop=%(stop)s '
            'position=%(position)s', {
                'rate': segment.rate,
                'format': Gst.Format.get_name(segment.format),
                'start': segment.start,
                'stop': segment.stop,
                'position': segment.position
            })
        position_ms = segment.position // Gst.MSECOND
        logger.debug('Audio event: position_changed(position=%r)', position_ms)
        AudioListener.send('position_changed', position=position_ms)


# TODO: create a player class which replaces the actors internals
class Audio(pykka.ThreadingActor):

    """
    Audio output through `GStreamer <http://gstreamer.freedesktop.org/>`_.
    """

    #: The GStreamer state mapped to :class:`mopidy.audio.PlaybackState`
    state = PlaybackState.STOPPED

    #: The software mixing interface :class:`mopidy.audio.actor.SoftwareMixer`
    mixer = None

    def __init__(self, config, mixer):
        super(Audio, self).__init__()

        self._config = config
        self._target_state = Gst.State.NULL
        self._buffering = False
        self._tags = {}
        self._pending_uri = None
        self._pending_tags = None
        self._pending_metadata = None

        self._playbin = None
        self._outputs = None
        self._queue = None
        self._about_to_finish_callback = None

        self._handler = _Handler(self)
        self._appsrc = _Appsrc()
        self._signals = utils.Signals()

        if mixer and self._config['audio']['mixer'] == 'software':
            self.mixer = SoftwareMixer(mixer)

    def on_start(self):
        self._thread = threading.current_thread()
        try:
            self._setup_preferences()
            self._setup_playbin()
            self._setup_outputs()
            self._setup_audio_sink()
        except GObject.GError as ex:
            logger.exception(ex)
            process.exit_process()

    def on_stop(self):
        self._teardown_mixer()
        self._teardown_playbin()

    def _setup_preferences(self):
        # TODO: move out of audio actor?
        # Fix for https://github.com/mopidy/mopidy/issues/604
        registry = Gst.Registry.get()
        jacksink = registry.find_feature('jackaudiosink', Gst.ElementFactory)
        if jacksink:
            jacksink.set_rank(Gst.Rank.SECONDARY)

    def _setup_playbin(self):
        playbin = Gst.ElementFactory.make('playbin')
        playbin.set_property('flags', _GST_PLAY_FLAGS_AUDIO)

        # TODO: turn into config values...
        playbin.set_property('buffer-size', 5 << 20)  # 5MB
        playbin.set_property('buffer-duration', 5 * Gst.SECOND)

        self._signals.connect(playbin, 'source-setup', self._on_source_setup)
        self._signals.connect(playbin, 'about-to-finish',
                              self._on_about_to_finish)

        self._playbin = playbin
        self._handler.setup_message_handling(playbin)

    def _teardown_playbin(self):
        self._handler.teardown_message_handling()
        self._handler.teardown_event_handling()
        self._signals.disconnect(self._playbin, 'about-to-finish')
        self._signals.disconnect(self._playbin, 'source-setup')
        self._playbin.set_state(Gst.State.NULL)

    def _setup_outputs(self):
        # We don't want to use outputs for regular testing, so just install
        # an unsynced fakesink when someone asks for a 'testoutput'.
        if self._config['audio']['output'] == 'testoutput':
            self._outputs = Gst.ElementFactory.make('fakesink')
        else:
            self._outputs = _Outputs()
            try:
                self._outputs.add_output(self._config['audio']['output'])
            except exceptions.AudioException:
                process.exit_process()  # TODO: move this up the chain

        self._handler.setup_event_handling(
            self._outputs.get_static_pad('sink'))

    def _setup_audio_sink(self):
        audio_sink = Gst.ElementFactory.make('bin', 'audio-sink')
        queue = Gst.ElementFactory.make('queue')
        volume = Gst.ElementFactory.make('volume')

        # Queue element to buy us time between the about-to-finish event and
        # the actual switch, i.e. about to switch can block for longer thanks
        # to this queue.

        # TODO: See if settings should be set to minimize latency. Previous
        # setting breaks appsrc, and settings before that broke on a few
        # systems. So leave the default to play it safe.
        if self._config['audio']['buffer_time'] > 0:
            queue.set_property(
                'max-size-time',
                self._config['audio']['buffer_time'] * Gst.MSECOND)

        audio_sink.add(queue)
        audio_sink.add(self._outputs)
        audio_sink.add(volume)

        queue.link(volume)
        volume.link(self._outputs)

        if self.mixer:
            self.mixer.setup(volume, self.actor_ref.proxy().mixer)

        ghost_pad = Gst.GhostPad.new('sink', queue.get_static_pad('sink'))
        audio_sink.add_pad(ghost_pad)

        self._playbin.set_property('audio-sink', audio_sink)
        self._queue = queue

    def _teardown_mixer(self):
        if self.mixer:
            self.mixer.teardown()

    def _on_about_to_finish(self, element):
        if self._thread == threading.current_thread():
            logger.error(
                'about-to-finish in actor, aborting to avoid deadlock.')
            return

        gst_logger.debug('Got about-to-finish event.')
        if self._about_to_finish_callback:
            logger.debug('Running about-to-finish callback.')
            self._about_to_finish_callback()

    def _on_source_setup(self, element, source):
        gst_logger.debug(
            'Got source-setup signal: element=%s', source.__class__.__name__)

        if source.get_factory().get_name() == 'appsrc':
            self._appsrc.configure(source)
        else:
            self._appsrc.reset()

        utils.setup_proxy(source, self._config['proxy'])

    def set_uri(self, uri):
        """
        Set URI of audio to be played.

        You *MUST* call :meth:`prepare_change` before calling this method.

        :param uri: the URI to play
        :type uri: string
        """

        # XXX: Hack to workaround issue on Mac OS X where volume level
        # does not persist between track changes. mopidy/mopidy#886
        if self.mixer is not None:
            current_volume = self.mixer.get_volume()
        else:
            current_volume = None

        self._pending_uri = uri
        self._pending_tags = {}
        self._playbin.set_property('uri', uri)

        if self.mixer is not None and current_volume is not None:
            self.mixer.set_volume(current_volume)

    def set_appsrc(
            self, caps, need_data=None, enough_data=None, seek_data=None):
        """
        Switch to using appsrc for getting audio to be played.

        You *MUST* call :meth:`prepare_change` before calling this method.

        :param caps: GStreamer caps string describing the audio format to
            expect
        :type caps: string
        :param need_data: callback for when appsrc needs data
        :type need_data: callable which takes data length hint in ms
        :param enough_data: callback for when appsrc has enough data
        :type enough_data: callable
        :param seek_data: callback for when data from a new position is needed
            to continue playback
        :type seek_data: callable which takes time position in ms
        """
        self._appsrc.prepare(
            Gst.Caps.from_string(caps), need_data, enough_data, seek_data)
        uri = 'appsrc://'
        self._pending_uri = uri
        self._playbin.set_property('uri', uri)

    def emit_data(self, buffer_):
        """
        Call this to deliver raw audio data to be played.

        If the buffer is :class:`None`, the end-of-stream token is put on the
        playbin. We will get a GStreamer message when the stream playback
        reaches the token, and can then do any end-of-stream related tasks.

        Note that the URI must be set to ``appsrc://`` for this to work.

        Returns :class:`True` if data was delivered.

        :param buffer_: buffer to pass to appsrc
        :type buffer_: :class:`Gst.Buffer` or :class:`None`
        :rtype: boolean
        """
        return self._appsrc.push(buffer_)

    def emit_end_of_stream(self):
        """
        Put an end-of-stream token on the playbin. This is typically used in
        combination with :meth:`emit_data`.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.

        .. deprecated:: 1.0
            Use :meth:`emit_data` with a :class:`None` buffer instead.
        """
        deprecation.warn('audio.emit_end_of_stream')
        self._appsrc.push(None)

    def set_about_to_finish_callback(self, callback):
        """
        Configure audio to use an about-to-finish callback.

        This should be used to achieve gapless playback. For this to work the
        callback *MUST* call :meth:`set_uri` with the new URI to play and
        block until this call has been made. :meth:`prepare_change` is not
        needed before :meth:`set_uri` in this one special case.

        :param callable callback: Callback to run when we need the next URI.
        """
        self._about_to_finish_callback = callback

    def get_position(self):
        """
        Get position in milliseconds.

        :rtype: int
        """
        success, position = self._playbin.query_position(Gst.Format.TIME)

        if not success:
            # TODO: take state into account for this and possibly also return
            # None as the unknown value instead of zero?
            logger.debug('Position query failed')
            return 0

        return utils.clocktime_to_millisecond(position)

    def set_position(self, position):
        """
        Set position in milliseconds.

        :param position: the position in milliseconds
        :type position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        # TODO: double check seek flags in use.
        gst_position = utils.millisecond_to_clocktime(position)
        gst_logger.debug('Sending flushing seek: position=%r', gst_position)
        # Send seek event to the queue not the playbin. The default behavior
        # for bins is to forward this event to all sinks. Which results in
        # duplicate seek events making it to appsrc. Since elements are not
        # allowed to act on the seek event, only modify it, this should be safe
        # to do.
        result = self._queue.seek_simple(
            Gst.Format.TIME, Gst.SeekFlags.FLUSH, gst_position)
        return result

    def start_playback(self):
        """
        Notify GStreamer that it should start playback.

        :rtype: :class:`True` if successfull, else :class:`False`
        """
        return self._set_state(Gst.State.PLAYING)

    def pause_playback(self):
        """
        Notify GStreamer that it should pause playback.

        :rtype: :class:`True` if successfull, else :class:`False`
        """
        return self._set_state(Gst.State.PAUSED)

    def prepare_change(self):
        """
        Notify GStreamer that we are about to change state of playback.

        This function *MUST* be called before changing URIs or doing
        changes like updating data that is being pushed. The reason for this
        is that GStreamer will reset all its state when it changes to
        :attr:`Gst.State.READY`.
        """
        return self._set_state(Gst.State.READY)

    def stop_playback(self):
        """
        Notify GStreamer that is should stop playback.

        :rtype: :class:`True` if successfull, else :class:`False`
        """
        self._buffering = False
        return self._set_state(Gst.State.NULL)

    def wait_for_state_change(self):
        """Block until any pending state changes are complete.

        Should only be used by tests.
        """
        self._playbin.get_state(timeout=Gst.CLOCK_TIME_NONE)

    def enable_sync_handler(self):
        """Enable manual processing of messages from bus.

        Should only be used by tests.
        """
        def sync_handler(bus, message):
            self._handler.on_message(bus, message)
            return Gst.BusSyncReply.DROP

        bus = self._playbin.get_bus()
        bus.set_sync_handler(sync_handler)

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

        :param state: State to set playbin to. One of: `Gst.State.NULL`,
            `Gst.State.READY`, `Gst.State.PAUSED` and `Gst.State.PLAYING`.
        :type state: :class:`Gst.State`
        :rtype: :class:`True` if successfull, else :class:`False`
        """
        self._target_state = state
        result = self._playbin.set_state(state)
        gst_logger.debug(
            'Changing state to %s: result=%s', state.value_name,
            result.value_name)

        if result == Gst.StateChangeReturn.FAILURE:
            logger.warning(
                'Setting GStreamer state to %s failed', state.value_name)
            return False
        # TODO: at this point we could already emit stopped event instead
        # of faking it in the message handling when result=OK
        return True

    # TODO: bake this into setup appsrc perhaps?
    def set_metadata(self, track):
        """
        Set track metadata for currently playing song.

        Only needs to be called by sources such as ``appsrc`` which do not
        already inject tags in playbin, e.g. when using :meth:`emit_data` to
        deliver raw audio data to GStreamer.

        :param track: the current track
        :type track: :class:`mopidy.models.Track`
        """
        taglist = Gst.TagList.new_empty()
        artists = [a for a in (track.artists or []) if a.name]

        def set_value(tag, value):
            gobject_value = GObject.Value()
            gobject_value.init(GObject.TYPE_STRING)
            gobject_value.set_string(value)
            taglist.add_value(Gst.TagMergeMode.REPLACE, tag, gobject_value)

        # Default to blank data to trick shoutcast into clearing any previous
        # values it might have.
        # TODO: Verify if this works at all, likely it doesn't.
        set_value(Gst.TAG_ARTIST, ' ')
        set_value(Gst.TAG_TITLE, ' ')
        set_value(Gst.TAG_ALBUM, ' ')

        if artists:
            set_value(Gst.TAG_ARTIST, ', '.join([a.name for a in artists]))

        if track.name:
            set_value(Gst.TAG_TITLE, track.name)

        if track.album and track.album.name:
            set_value(Gst.TAG_ALBUM, track.album.name)

        gst_logger.debug(
            'Sending TAG event for track %r: %r',
            track.uri, taglist.to_string())
        event = Gst.Event.new_tag(taglist)
        if self._pending_uri:
            self._pending_metadata = event
        else:
            self._playbin.send_event(event)

    def get_current_tags(self):
        """
        Get the currently playing media's tags.

        If no tags have been found, or nothing is playing this returns an empty
        dictionary. For each set of tags we collect a tags_changed event is
        emitted with the keys of the changes tags. After such calls users may
        call this function to get the updated values.

        :rtype: {key: [values]} dict for the current media.
        """
        # TODO: should this be a (deep) copy? most likely yes
        # TODO: should we return None when stopped?
        # TODO: support only fetching keys we care about?
        return self._tags
