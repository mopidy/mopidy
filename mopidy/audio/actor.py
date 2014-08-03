from __future__ import unicode_literals

import logging

import gobject

import pygst
pygst.require('0.10')
import gst  # noqa
import gst.pbutils

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

MB = 1 << 20

# GST_PLAY_FLAG_VIDEO (1<<0)
# GST_PLAY_FLAG_AUDIO (1<<1)
# GST_PLAY_FLAG_TEXT (1<<2)
# GST_PLAY_FLAG_VIS (1<<3)
# GST_PLAY_FLAG_SOFT_VOLUME (1<<4)
# GST_PLAY_FLAG_NATIVE_AUDIO (1<<5)
# GST_PLAY_FLAG_NATIVE_VIDEO (1<<6)
# GST_PLAY_FLAG_DOWNLOAD (1<<7)
# GST_PLAY_FLAG_BUFFERING (1<<8)
# GST_PLAY_FLAG_DEINTERLACE (1<<9)
# GST_PLAY_FLAG_SOFT_COLORBALANCE (1<<10)

# Default flags to use for playbin: AUDIO, SOFT_VOLUME, DOWNLOAD
PLAYBIN_FLAGS = (1 << 1) | (1 << 4) | (1 << 7)
PLAYBIN_VIS_FLAGS = PLAYBIN_FLAGS | (1 << 3)


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
        source.set_property('max-bytes', 1 * MB)
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
        return self._source.emit('push-buffer', buffer_) == gst.FLOW_OK

    def end_of_stream(self):
        self._source.emit('end-of-stream')

    def _on_signal(self, element, clocktime, func):
        # This shim is used to ensure we always return true, and also handles
        # that not all the callbacks have a time argument.
        if clocktime is None:
            func()
        else:
            func(utils.clocktime_to_millisecond(clocktime))
        return True


class _Outputs(gst.Bin):
    def __init__(self):
        gst.Bin.__init__(self)

        self._tee = gst.element_factory_make('tee')
        self.add(self._tee)

        # Queue element to buy us time between the about to finish event and
        # the actual switch, i.e. about to switch can block for longer thanks
        # to this queue.
        # TODO: make the min-max values a setting?
        # TODO: move out of this class?
        queue = gst.element_factory_make('queue')
        queue.set_property('max-size-buffers', 0)
        queue.set_property('max-size-bytes', 0)
        queue.set_property('max-size-time', 5 * gst.SECOND)
        queue.set_property('min-threshold-time', 3 * gst.SECOND)
        self.add(queue)

        queue.link(self._tee)

        ghost_pad = gst.GhostPad('sink', queue.get_pad('sink'))
        self.add_pad(ghost_pad)

        # Add an always connected fakesink so the tee doesn't fail.
        # XXX disabled for now as we get one stream changed per sink...
        # self._add(gst.element_factory_make('fakesink'))

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
        # All tee branches need a queue in front of them.
        queue = gst.element_factory_make('queue')
        self.add(element)
        self.add(queue)
        queue.link(element)
        self._tee.link(queue)


def setup_proxy(element, config):
    # TODO: reuse in scanner code
    if not config.get('hostname'):
        return

    proxy = "%s://%s:%d" % (config.get('scheme', 'http'),
                            config.get('hostname'),
                            config.get('port', 80))

    element.set_property('proxy', proxy)
    element.set_property('proxy-id', config.get('username'))
    element.set_property('proxy-pw', config.get('password'))


# TODO: create a player class which replaces the actors internals
class Audio(pykka.ThreadingActor):
    """
    Audio output through `GStreamer <http://gstreamer.freedesktop.org/>`_.
    """

    #: The GStreamer state mapped to :class:`mopidy.audio.PlaybackState`
    state = PlaybackState.STOPPED

    def __init__(self, config, mixer):
        super(Audio, self).__init__()

        self._config = config
        self._mixer = mixer
        self._target_state = gst.STATE_NULL
        self._buffering = False

        self._playbin = None
        self._outputs = None
        self._about_to_finish_callback = None

        self._appsrc = _Appsrc()
        self._signals = _Signals()

    def on_start(self):
        try:
            self._setup_preferences()
            self._setup_playbin()
            self._setup_output()
            self._setup_mixer()
            self._setup_visualizer()
            self._setup_message_processor()
        except gobject.GError as ex:
            logger.exception(ex)
            process.exit_process()

    def on_stop(self):
        self._teardown_message_processor()
        self._teardown_mixer()
        self._teardown_playbin()

    def _setup_preferences(self):
        # Fix for https://github.com/mopidy/mopidy/issues/604
        registry = gst.registry_get_default()
        jacksink = registry.find_feature(
            'jackaudiosink', gst.TYPE_ELEMENT_FACTORY)
        if jacksink:
            jacksink.set_rank(gst.RANK_SECONDARY)

    def _setup_playbin(self):
        playbin = gst.element_factory_make('playbin2')
        playbin.set_property('flags', PLAYBIN_FLAGS)

        playbin.set_property('buffer-size', 2*1024*1024)
        playbin.set_property('buffer-duration', 2*gst.SECOND)

        self._signals.connect(playbin, 'source-setup', self._on_source_setup)
        self._signals.connect(
            playbin, 'about-to-finish', self._on_about_to_finish)

        self._playbin = playbin

    def _on_about_to_finish(self, element):
        gst_logger.debug('Got about-to-finish event.')
        if self._about_to_finish_callback:
            self._about_to_finish_callback()

    def _on_source_setup(self, element, source):
        gst_logger.debug('Got source-setup: element=%s', source)

        if source.get_factory().get_name() == 'appsrc':
            self._appsrc.configure(source)
        else:
            self._appsrc.reset()

        if hasattr(source.props, 'proxy'):
            setup_proxy(source, self._config['proxy'])

    def _teardown_playbin(self):
        self._signals.disconnect(self._playbin, 'about-to-finish')
        self._signals.disconnect(self._playbin, 'notify::source')
        self._signals.disconnect(self._playbin, 'source-setup')
        self._playbin.set_state(gst.STATE_NULL)

    def _setup_output(self):
        self._outputs = _Outputs()
        self._outputs.get_pad('sink').add_event_probe(self._on_pad_event)
        try:
            self._outputs.add_output(self._config['audio']['output'])
        except exceptions.AudioException:
            process.exit_process()  # TODO: move this up the chain
        self._playbin.set_property('audio-sink', self._outputs)

    def _setup_mixer(self):
        if self._config['audio']['mixer'] != 'software':
            return
        self._mixer.audio = self.actor_ref.proxy()
        self._signals.connect(
            self._playbin, 'notify::volume', self._on_mixer_change)
        self._signals.connect(
            self._playbin, 'notify::mute', self._on_mixer_change)

        # The Mopidy startup procedure will set the initial volume of a mixer,
        # but this happens before the audio actor is injected into the software
        # mixer and has no effect. Thus, we need to set the initial volume
        # again.
        initial_volume = self._config['audio']['mixer_volume']
        if initial_volume is not None:
            self._mixer.set_volume(initial_volume)

    def _on_mixer_change(self, element, gparamspec):
        self._mixer.trigger_events_for_changed_values()

    def _teardown_mixer(self):
        if self._config['audio']['mixer'] != 'software':
            return
        self._signals.disconnect(self._playbin, 'notify::volume')
        self._signals.disconnect(self._playbin, 'notify::mute')
        self._mixer.audio = None

    def _setup_visualizer(self):
        visualizer_element = self._config['audio']['visualizer']
        if not visualizer_element:
            return
        try:
            visualizer = gst.element_factory_make(visualizer_element)
            self._playbin.set_property('vis-plugin', visualizer)
            self._playbin.set_property('flags', PLAYBIN_VIS_FLAGS)
            logger.info('Audio visualizer set to "%s"', visualizer_element)
        except gobject.GError as ex:
            logger.error(
                'Failed to create audio visualizer "%s": %s',
                visualizer_element, ex)

    def _setup_message_processor(self):
        bus = self._playbin.get_bus()
        bus.add_signal_watch()
        self._signals.connect(bus, 'message', self._on_message)

    def _teardown_message_processor(self):
        bus = self._playbin.get_bus()
        self._signals.disconnect(bus, 'message')
        bus.remove_signal_watch()

    def _on_pad_event(self, pad, event):
        if event.type == gst.EVENT_NEWSEGMENT:
            update, rate, format_, start, stop, pos = event.parse_new_segment()
            gst_logger.debug('Got new-segment event: update=%s rate=%s '
                             'format=%s start=%s stop=%s position=%s', update,
                             rate, format_.value_name, start, stop, pos)
            pos_ms = pos // gst.MSECOND
            logger.debug('Triggering: position_changed(position=%s)', pos_ms)
            AudioListener.send('position_changed', position=pos_ms)

        return True

    def _on_message(self, bus, msg):
        if msg.type == gst.MESSAGE_STATE_CHANGED and msg.src == self._playbin:
            self._on_playbin_state_changed(*msg.parse_state_changed())
        elif msg.type == gst.MESSAGE_BUFFERING:
            self._on_buffering(msg.parse_buffering())
        elif msg.type == gst.MESSAGE_EOS:
            self._on_end_of_stream()
        elif msg.type == gst.MESSAGE_ERROR:
            self._on_error(*msg.parse_error())
        elif msg.type == gst.MESSAGE_WARNING:
            self._on_warning(*msg.parse_warning())
        elif msg.type == gst.MESSAGE_ASYNC_DONE:
            gst_logger.debug('Got async-done message.')
        elif msg.type == gst.MESSAGE_ELEMENT:
            if msg.structure.has_name('playbin2-stream-changed'):
                self._on_stream_changed(msg.structure['uri'])
            elif gst.pbutils.is_missing_plugin_message(msg):
                self._on_missing_plugin(msg)

    def _on_playbin_state_changed(self, old_state, new_state, pending_state):
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
        old_state, self.state = self.state, new_state

        target_state = _GST_STATE_MAPPING[self._target_state]
        if target_state == new_state:
            target_state = None

        logger.debug('Triggering: state_changed(old_state=%s, new_state=%s, '
                     'target_state=%s)', old_state, new_state, target_state)
        AudioListener.send('state_changed', old_state=old_state,
                           new_state=new_state, target_state=target_state)
        if new_state == PlaybackState.STOPPED:
            logger.debug('Triggering: stream_changed(uri=None)')
            AudioListener.send('stream_changed', uri=None)

    def _on_buffering(self, percent):
        gst_logger.debug('Got buffering message: percent=%d%%', percent)

        if percent < 10 and not self._buffering:
            self._playbin.set_state(gst.STATE_PAUSED)
            self._buffering = True
        if percent == 100:
            self._buffering = False
            if self._target_state == gst.STATE_PLAYING:
                self._playbin.set_state(gst.STATE_PLAYING)

    def _on_end_of_stream(self):
        gst_logger.debug('Got end-of-stream message.')
        logger.debug('Triggering: reached_end_of_stream()')
        AudioListener.send('reached_end_of_stream')

    def _on_error(self, error, debug):
        gst_logger.error(str(error).decode('utf-8'))
        if debug:
            gst_logger.debug(debug.decode('utf-8'))
        # TODO: is this needed?
        self.stop_playback()

    def _on_warning(self, error, debug):
        gst_logger.warning(str(error).decode('utf-8'))
        if debug:
            gst_logger.debug(debug.decode('utf-8'))

    def _on_stream_changed(self, uri):
        gst_logger.debug('Got stream-changed message: uri:%s', uri)
        logger.debug('Triggering: stream_changed(uri=%s)', uri)
        AudioListener.send('stream_changed', uri=uri)

    def _on_missing_plugin(self, msg):
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

    def set_uri(self, uri):
        """
        Set URI of audio to be played.

        You *MUST* call :meth:`prepare_change` before calling this method.

        :param uri: the URI to play
        :type uri: string
        """
        self._playbin.set_property('uri', uri)

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

        Note that the uri must be set to ``appsrc://`` for this to work.

        Returns true if data was delivered.

        :param buffer_: buffer to pass to appsrc
        :type buffer_: :class:`gst.Buffer`
        :rtype: boolean
        """
        return self._appsrc.push(buffer_)

    def emit_end_of_stream(self):
        """
        Put an end-of-stream token on the playbin. This is typically used in
        combination with :meth:`emit_data`.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.
        """
        self._appsrc.end_of_stream()
        gst_logger.debug('Sent appsrc end-of-stream event.')

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
            logger.debug('Position query failed')
            return 0

    def set_position(self, position):
        """
        Set position in milliseconds.

        :param position: the position in milliseconds
        :type position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
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
            self._on_message(bus, message)
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

    def get_volume(self):
        """
        Get volume level of the software mixer.

        Example values:

        0:
            Minimum volume.
        100:
            Maximum volume.

        :rtype: int in range [0..100]
        """
        return int(round(self._playbin.get_property('volume') * 100))

    def set_volume(self, volume):
        """
        Set volume level of the software mixer.

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self._playbin.set_property('volume', volume / 100.0)
        return True

    def get_mute(self):
        """
        Get mute status of the software mixer.

        :rtype: :class:`True` if muted, :class:`False` if unmuted,
          :class:`None` if no mixer is installed.
        """
        return self._playbin.get_property('mute')

    def set_mute(self, mute):
        """
        Mute or unmute of the software mixer.

        :param mute: Whether to mute the mixer or not.
        :type mute: bool
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self._playbin.set_property('mute', bool(mute))
        return True

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
        self._playbin.send_event(event)
        gst_logger.debug('Sent tag event: track=%s', track.uri)
