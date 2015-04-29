from __future__ import absolute_import, unicode_literals

import logging
import os

import gobject

import pygst
pygst.require('0.10')
import gst  # noqa
import gst.pbutils  # noqa

import pykka

from mopidy import exceptions
from mopidy.audio import playlists, utils
from mopidy.audio.constants import PlaybackState
from mopidy.audio.listener import AudioListener
from mopidy.utils import process


logger = logging.getLogger(__name__)

# This logger is only meant for debug logging of low level gstreamer info such
# as callbacks, event, messages and direct interaction with GStreamer such as
# set_state on a pipeline.
gst_logger = logging.getLogger('mopidy.audio.gst')

playlists.register_typefinders()
playlists.register_elements()

_GST_STATE_MAPPING = {
    gst.STATE_PLAYING: PlaybackState.PLAYING,
    gst.STATE_PAUSED: PlaybackState.PAUSED,
    gst.STATE_NULL: PlaybackState.STOPPED}


class _Signals(object):
    """Helper for tracking gobject signal registrations"""
    def __init__(self):
        self._ids = {}

    def connect(self, element, event, func, *args):
        """Connect a function + args to signal event on an element.

        Each event may only be handled by one callback in this implementation.
        """
        assert (element, event) not in self._ids
        self._ids[(element, event)] = element.connect(event, func, *args)

    def disconnect(self, element, event):
        """Disconnect whatever handler we have for and element+event pair.

        Does nothing it the handler has already been removed.
        """
        signal_id = self._ids.pop((element, event), None)
        if signal_id is not None:
            element.disconnect(signal_id)

    def clear(self):
        """Clear all registered signal handlers."""
        for element, event in self._ids.keys():
            element.disconnect(self._ids.pop((element, event)))


# TODO: expose this as a property on audio?
class _Appsrc(object):
    """Helper class for dealing with appsrc based playback."""
    def __init__(self):
        self._signals = _Signals()
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
            return self._source.emit('end-of-stream') == gst.FLOW_OK
        else:
            return self._source.emit('push-buffer', buffer_) == gst.FLOW_OK

    def _on_signal(self, element, clocktime, func):
        # This shim is used to ensure we always return true, and also handles
        # that not all the callbacks have a time argument.
        if clocktime is None:
            func()
        else:
            func(utils.clocktime_to_millisecond(clocktime))
        return True


# TODO: expose this as a property on audio when #790 gets further along.
class _Outputs(gst.Bin):
    def __init__(self):
        gst.Bin.__init__(self, 'outputs')

        self._tee = gst.element_factory_make('tee')
        self.add(self._tee)

        ghost_pad = gst.GhostPad('sink', self._tee.get_pad('sink'))
        self.add_pad(ghost_pad)

        # Add an always connected fakesink which respects the clock so the tee
        # doesn't fail even if we don't have any outputs.
        fakesink = gst.element_factory_make('fakesink')
        fakesink.set_property('sync', True)
        self._add(fakesink)

    def add_output(self, description):
        # XXX This only works for pipelines not in use until #790 gets done.
        try:
            output = gst.parse_bin_from_description(
                description, ghost_unconnected_pads=True)
        except gobject.GError as ex:
            logger.error(
                'Failed to create audio output "%s": %s', description, ex)
            raise exceptions.AudioException(bytes(ex))

        self._add(output)
        logger.info('Audio output set to "%s"', description)

    def _add(self, element):
        queue = gst.element_factory_make('queue')
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
        self._signals = _Signals()

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
        self._event_handler_id = pad.add_event_probe(self.on_event)

    def teardown_message_handling(self):
        bus = self._element.get_bus()
        bus.remove_signal_watch()
        bus.disconnect(self._message_handler_id)
        self._message_handler_id = None

    def teardown_event_handling(self):
        self._pad.remove_event_probe(self._event_handler_id)
        self._event_handler_id = None

    def on_message(self, bus, msg):
        if msg.type == gst.MESSAGE_STATE_CHANGED and msg.src == self._element:
            self.on_playbin_state_changed(*msg.parse_state_changed())
        elif msg.type == gst.MESSAGE_BUFFERING:
            self.on_buffering(msg.parse_buffering(), msg.structure)
        elif msg.type == gst.MESSAGE_EOS:
            self.on_end_of_stream()
        elif msg.type == gst.MESSAGE_ERROR:
            self.on_error(*msg.parse_error())
        elif msg.type == gst.MESSAGE_WARNING:
            self.on_warning(*msg.parse_warning())
        elif msg.type == gst.MESSAGE_ASYNC_DONE:
            self.on_async_done()
        elif msg.type == gst.MESSAGE_TAG:
            self.on_tag(msg.parse_tag())
        elif msg.type == gst.MESSAGE_ELEMENT:
            if gst.pbutils.is_missing_plugin_message(msg):
                self.on_missing_plugin(msg)

    def on_event(self, pad, event):
        if event.type == gst.EVENT_NEWSEGMENT:
            self.on_new_segment(*event.parse_new_segment())
        elif event.type == gst.EVENT_SINK_MESSAGE:
            # Handle stream changed messages when they reach our output bin.
            # If we listen for it on the bus we get one per tee branch.
            msg = event.parse_sink_message()
            if msg.structure.has_name('playbin2-stream-changed'):
                self.on_stream_changed(msg.structure['uri'])
        return True

    def on_playbin_state_changed(self, old_state, new_state, pending_state):
        gst_logger.debug('Got state-changed message: old=%s new=%s pending=%s',
                         old_state.value_name, new_state.value_name,
                         pending_state.value_name)

        if new_state == gst.STATE_READY and pending_state == gst.STATE_NULL:
            # XXX: We're not called on the last state change when going down to
            # NULL, so we rewrite the second to last call to get the expected
            # behavior.
            new_state = gst.STATE_NULL
            pending_state = gst.STATE_VOID_PENDING

        if pending_state != gst.STATE_VOID_PENDING:
            return  # Ignore intermediate state changes

        if new_state == gst.STATE_READY:
            return  # Ignore READY state as it's GStreamer specific

        new_state = _GST_STATE_MAPPING[new_state]
        old_state, self._audio.state = self._audio.state, new_state

        target_state = _GST_STATE_MAPPING[self._audio._target_state]
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
            gst.DEBUG_BIN_TO_DOT_FILE(
                self._audio._playbin, gst.DEBUG_GRAPH_SHOW_ALL, 'mopidy')

    def on_buffering(self, percent, structure=None):
        if structure and structure.has_field('buffering-mode'):
            if structure['buffering-mode'] == gst.BUFFERING_LIVE:
                return  # Live sources stall in paused.

        level = logging.getLevelName('TRACE')
        if percent < 10 and not self._audio._buffering:
            self._audio._playbin.set_state(gst.STATE_PAUSED)
            self._audio._buffering = True
            level = logging.DEBUG
        if percent == 100:
            self._audio._buffering = False
            if self._audio._target_state == gst.STATE_PLAYING:
                self._audio._playbin.set_state(gst.STATE_PLAYING)
            level = logging.DEBUG

        gst_logger.log(level, 'Got buffering message: percent=%d%%', percent)

    def on_end_of_stream(self):
        gst_logger.debug('Got end-of-stream message.')
        logger.debug('Audio event: reached_end_of_stream()')
        self._audio._tags = {}
        AudioListener.send('reached_end_of_stream')

    def on_error(self, error, debug):
        gst_logger.error(str(error).decode('utf-8'))
        if debug:
            gst_logger.debug(debug.decode('utf-8'))
        # TODO: is this needed?
        self._audio.stop_playback()

    def on_warning(self, error, debug):
        gst_logger.warning(str(error).decode('utf-8'))
        if debug:
            gst_logger.debug(debug.decode('utf-8'))

    def on_async_done(self):
        gst_logger.debug('Got async-done.')

    def on_tag(self, taglist):
        tags = utils.convert_taglist(taglist)
        self._audio._tags.update(tags)
        logger.debug('Audio event: tags_changed(tags=%r)', tags.keys())
        AudioListener.send('tags_changed', tags=tags.keys())

    def on_missing_plugin(self, msg):
        desc = gst.pbutils.missing_plugin_message_get_description(msg)
        debug = gst.pbutils.missing_plugin_message_get_installer_detail(msg)

        gst_logger.debug('Got missing-plugin message: description:%s', desc)
        logger.warning('Could not find a %s to handle media.', desc)
        if gst.pbutils.install_plugins_supported():
            logger.info('You might be able to fix this by running: '
                        'gst-installer "%s"', debug)
        # TODO: store the missing plugins installer info in a file so we can
        # can provide a 'mopidy install-missing-plugins' if the system has the
        # required helper installed?

    def on_new_segment(self, update, rate, format_, start, stop, position):
        gst_logger.debug('Got new-segment event: update=%s rate=%s format=%s '
                         'start=%s stop=%s position=%s', update, rate,
                         format_.value_name, start, stop, position)
        position_ms = position // gst.MSECOND
        logger.debug('Audio event: position_changed(position=%s)', position_ms)
        AudioListener.send('position_changed', position=position_ms)

    def on_stream_changed(self, uri):
        gst_logger.debug('Got stream-changed message: uri=%s', uri)
        logger.debug('Audio event: stream_changed(uri=%s)', uri)
        AudioListener.send('stream_changed', uri=uri)


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
        self._target_state = gst.STATE_NULL
        self._buffering = False
        self._tags = {}

        self._playbin = None
        self._outputs = None
        self._about_to_finish_callback = None

        self._handler = _Handler(self)
        self._appsrc = _Appsrc()
        self._signals = _Signals()

        if mixer and self._config['audio']['mixer'] == 'software':
            self.mixer = SoftwareMixer(mixer)

    def on_start(self):
        try:
            self._setup_preferences()
            self._setup_playbin()
            self._setup_outputs()
            self._setup_audio_sink()
        except gobject.GError as ex:
            logger.exception(ex)
            process.exit_process()

    def on_stop(self):
        self._teardown_mixer()
        self._teardown_playbin()

    def _setup_preferences(self):
        # TODO: move out of audio actor?
        # Fix for https://github.com/mopidy/mopidy/issues/604
        registry = gst.registry_get_default()
        jacksink = registry.find_feature(
            'jackaudiosink', gst.TYPE_ELEMENT_FACTORY)
        if jacksink:
            jacksink.set_rank(gst.RANK_SECONDARY)

    def _setup_playbin(self):
        playbin = gst.element_factory_make('playbin2')
        playbin.set_property('flags', 2)  # GST_PLAY_FLAG_AUDIO

        # TODO: turn into config values...
        playbin.set_property('buffer-size', 5 << 20)  # 5MB
        playbin.set_property('buffer-duration', 5 * gst.SECOND)

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
        self._playbin.set_state(gst.STATE_NULL)

    def _setup_outputs(self):
        # We don't want to use outputs for regular testing, so just install
        # an unsynced fakesink when someone asks for a 'testoutput'.
        if self._config['audio']['output'] == 'testoutput':
            self._outputs = gst.element_factory_make('fakesink')
        else:
            self._outputs = _Outputs()
            try:
                self._outputs.add_output(self._config['audio']['output'])
            except exceptions.AudioException:
                process.exit_process()  # TODO: move this up the chain

        self._handler.setup_event_handling(self._outputs.get_pad('sink'))

    def _setup_audio_sink(self):
        audio_sink = gst.Bin('audio-sink')

        # Queue element to buy us time between the about to finish event and
        # the actual switch, i.e. about to switch can block for longer thanks
        # to this queue.
        # TODO: make the min-max values a setting?
        queue = gst.element_factory_make('queue')
        queue.set_property('max-size-buffers', 0)
        queue.set_property('max-size-bytes', 0)
        queue.set_property('max-size-time', 3 * gst.SECOND)
        queue.set_property('min-threshold-time', 1 * gst.SECOND)

        audio_sink.add(queue)
        audio_sink.add(self._outputs)

        if self.mixer:
            volume = gst.element_factory_make('volume')
            audio_sink.add(volume)
            queue.link(volume)
            volume.link(self._outputs)
            self.mixer.setup(volume, self.actor_ref.proxy().mixer)
        else:
            queue.link(self._outputs)

        ghost_pad = gst.GhostPad('sink', queue.get_pad('sink'))
        audio_sink.add_pad(ghost_pad)

        self._playbin.set_property('audio-sink', audio_sink)

    def _teardown_mixer(self):
        if self.mixer:
            self.mixer.teardown()

    def _on_about_to_finish(self, element):
        gst_logger.debug('Got about-to-finish event.')
        if self._about_to_finish_callback:
            logger.debug('Running about to finish callback.')
            self._about_to_finish_callback()

    def _on_source_setup(self, element, source):
        gst_logger.debug('Got source-setup: element=%s', source)

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

        self._tags = {}  # TODO: add test for this somehow
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
            gst.Caps(bytes(caps)), need_data, enough_data, seek_data)
        self._playbin.set_property('uri', 'appsrc://')

    def emit_data(self, buffer_):
        """
        Call this to deliver raw audio data to be played.

        If the buffer is :class:`None`, the end-of-stream token is put on the
        playbin. We will get a GStreamer message when the stream playback
        reaches the token, and can then do any end-of-stream related tasks.

        Note that the URI must be set to ``appsrc://`` for this to work.

        Returns :class:`True` if data was delivered.

        :param buffer_: buffer to pass to appsrc
        :type buffer_: :class:`gst.Buffer` or :class:`None`
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
        try:
            gst_position = self._playbin.query_position(gst.FORMAT_TIME)[0]
            return utils.clocktime_to_millisecond(gst_position)
        except gst.QueryError:
            # TODO: take state into account for this and possibly also return
            # None as the unknown value instead of zero?
            logger.debug('Position query failed')
            return 0

    def set_position(self, position):
        """
        Set position in milliseconds.

        :param position: the position in milliseconds
        :type position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        # TODO: double check seek flags in use.
        gst_position = utils.millisecond_to_clocktime(position)
        result = self._playbin.seek_simple(
            gst.Format(gst.FORMAT_TIME), gst.SEEK_FLAG_FLUSH, gst_position)
        gst_logger.debug('Sent flushing seek: position=%s', gst_position)
        return result

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
        self._buffering = False
        return self._set_state(gst.STATE_NULL)

    def wait_for_state_change(self):
        """Block until any pending state changes are complete.

        Should only be used by tests.
        """
        self._playbin.get_state()

    def enable_sync_handler(self):
        """Enable manual processing of messages from bus.

        Should only be used by tests.
        """
        def sync_handler(bus, message):
            self._handler.on_message(bus, message)
            return gst.BUS_DROP

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

        :param state: State to set playbin to. One of: `gst.STATE_NULL`,
            `gst.STATE_READY`, `gst.STATE_PAUSED` and `gst.STATE_PLAYING`.
        :type state: :class:`gst.State`
        :rtype: :class:`True` if successfull, else :class:`False`
        """
        self._target_state = state
        result = self._playbin.set_state(state)
        gst_logger.debug('State change to %s: result=%s', state.value_name,
                         result.value_name)

        if result == gst.STATE_CHANGE_FAILURE:
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

        Only needs to be called by sources such as `appsrc` which do not
        already inject tags in playbin, e.g. when using :meth:`emit_data` to
        deliver raw audio data to GStreamer.

        :param track: the current track
        :type track: :class:`mopidy.models.Track`
        """
        taglist = gst.TagList()
        artists = [a for a in (track.artists or []) if a.name]

        # Default to blank data to trick shoutcast into clearing any previous
        # values it might have.
        taglist[gst.TAG_ARTIST] = ' '
        taglist[gst.TAG_TITLE] = ' '
        taglist[gst.TAG_ALBUM] = ' '

        if artists:
            taglist[gst.TAG_ARTIST] = ', '.join([a.name for a in artists])

        if track.name:
            taglist[gst.TAG_TITLE] = track.name

        if track.album and track.album.name:
            taglist[gst.TAG_ALBUM] = track.album.name

        event = gst.event_new_tag(taglist)
        # TODO: check if we get this back on our own bus?
        self._playbin.send_event(event)
        gst_logger.debug('Sent tag event: track=%s', track.uri)

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
