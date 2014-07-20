from __future__ import unicode_literals

import logging

import gobject

import pygst
pygst.require('0.10')
import gst  # noqa

import pykka

from mopidy.audio import playlists, utils
from mopidy.audio.constants import PlaybackState
from mopidy.audio.listener import AudioListener
from mopidy.utils import process


logger = logging.getLogger(__name__)

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
        self._signal_ids = {}  # {(element, event): signal_id}

        self._appsrc = None
        self._appsrc_caps = None
        self._appsrc_need_data_callback = None
        self._appsrc_enough_data_callback = None
        self._appsrc_seek_data_callback = None

    def on_start(self):
        try:
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

    def _connect(self, element, event, *args):
        """Helper to keep track of signal ids based on element+event"""
        self._signal_ids[(element, event)] = element.connect(event, *args)

    def _disconnect(self, element, event):
        """Helper to disconnect signals created with _connect helper."""
        signal_id = self._signal_ids.pop((element, event), None)
        if signal_id is not None:
            element.disconnect(signal_id)

    def _setup_playbin(self):
        playbin = gst.element_factory_make('playbin2')
        playbin.set_property('flags', PLAYBIN_FLAGS)

        playbin.set_property('buffer-size', 2*1024*1024)
        playbin.set_property('buffer-duration', 2*gst.SECOND)

        self._connect(playbin, 'about-to-finish', self._on_about_to_finish)
        self._connect(playbin, 'notify::source', self._on_new_source)
        self._connect(playbin, 'source-setup', self._on_source_setup)

        self._playbin = playbin

    def _on_about_to_finish(self, element):
        source, self._appsrc = self._appsrc, None
        if source is None:
            return
        self._appsrc_caps = None

        self._disconnect(source, 'need-data')
        self._disconnect(source, 'enough-data')
        self._disconnect(source, 'seek-data')

    def _on_new_source(self, element, pad):
        uri = element.get_property('uri')
        if not uri or not uri.startswith('appsrc://'):
            return

        source = element.get_property('source')
        source.set_property('caps', self._appsrc_caps)
        source.set_property('format', b'time')
        source.set_property('stream-type', b'seekable')
        source.set_property('max-bytes', 1 * MB)
        source.set_property('min-percent', 50)

        self._connect(source, 'need-data', self._appsrc_on_need_data)
        self._connect(source, 'enough-data', self._appsrc_on_enough_data)
        self._connect(source, 'seek-data', self._appsrc_on_seek_data)

        self._appsrc = source

    def _on_source_setup(self, element, source):
        scheme = 'http'
        hostname = self._config['proxy']['hostname']
        port = 80

        if hasattr(source.props, 'proxy') and hostname:
            if self._config['proxy']['port']:
                port = self._config['proxy']['port']
            if self._config['proxy']['scheme']:
                scheme = self._config['proxy']['scheme']

            proxy = "%s://%s:%d" % (scheme, hostname, port)
            source.set_property('proxy', proxy)
            source.set_property('proxy-id', self._config['proxy']['username'])
            source.set_property('proxy-pw', self._config['proxy']['password'])

    def _appsrc_on_need_data(self, appsrc, gst_length_hint):
        length_hint = utils.clocktime_to_millisecond(gst_length_hint)
        if self._appsrc_need_data_callback is not None:
            self._appsrc_need_data_callback(length_hint)
        return True

    def _appsrc_on_enough_data(self, appsrc):
        if self._appsrc_enough_data_callback is not None:
            self._appsrc_enough_data_callback()
        return True

    def _appsrc_on_seek_data(self, appsrc, gst_position):
        position = utils.clocktime_to_millisecond(gst_position)
        if self._appsrc_seek_data_callback is not None:
            self._appsrc_seek_data_callback(position)
        return True

    def _teardown_playbin(self):
        self._disconnect(self._playbin, 'about-to-finish')
        self._disconnect(self._playbin, 'notify::source')
        self._disconnect(self._playbin, 'source-setup')
        self._playbin.set_state(gst.STATE_NULL)

    def _setup_output(self):
        output_desc = self._config['audio']['output']
        try:
            output = gst.parse_bin_from_description(
                output_desc, ghost_unconnected_pads=True)
            self._playbin.set_property('audio-sink', output)
            logger.info('Audio output set to "%s"', output_desc)
        except gobject.GError as ex:
            logger.error(
                'Failed to create audio output "%s": %s', output_desc, ex)
            process.exit_process()

    def _setup_mixer(self):
        if self._config['audio']['mixer'] != 'software':
            return
        self._mixer.audio = self.actor_ref.proxy()
        self._connect(self._playbin, 'notify::volume', self._on_mixer_change)
        self._connect(self._playbin, 'notify::mute', self._on_mixer_change)

    def _on_mixer_change(self, element, gparamspec):
        self._mixer.trigger_events_for_changed_values()

    def _teardown_mixer(self):
        if self._config['audio']['mixer'] != 'software':
            return
        self._disconnect(self._playbin, 'notify::volume')
        self._disconnect(self._playbin, 'notify::mute')
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
        self._connect(bus, 'message', self._on_message)

    def _teardown_message_processor(self):
        bus = self._playbin.get_bus()
        self._disconnect(bus, 'message')
        bus.remove_signal_watch()

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

    def _on_playbin_state_changed(self, old_state, new_state, pending_state):
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

        logger.debug(
            'Triggering event: state_changed(old_state=%s, new_state=%s, '
            'target_state=%s)', old_state, new_state, target_state)
        AudioListener.send('state_changed', old_state=old_state,
                           new_state=new_state, target_state=target_state)

    def _on_buffering(self, percent):
        if percent < 10 and not self._buffering:
            self._playbin.set_state(gst.STATE_PAUSED)
            self._buffering = True
        if percent == 100:
            self._buffering = False
            if self._target_state == gst.STATE_PLAYING:
                self._playbin.set_state(gst.STATE_PLAYING)

        logger.debug('Buffer %d%% full', percent)

    def _on_end_of_stream(self):
        logger.debug('Triggering reached_end_of_stream event')
        AudioListener.send('reached_end_of_stream')

    def _on_error(self, error, debug):
        logger.error(
            '%s Debug message: %s',
            str(error).decode('utf-8'), debug.decode('utf-8') or 'None')
        self.stop_playback()

    def _on_warning(self, error, debug):
        logger.warning(
            '%s Debug message: %s',
            str(error).decode('utf-8'), debug.decode('utf-8') or 'None')

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
        if isinstance(caps, unicode):
            caps = caps.encode('utf-8')
        self._appsrc_caps = gst.Caps(caps)
        self._appsrc_need_data_callback = need_data
        self._appsrc_enough_data_callback = enough_data
        self._appsrc_seek_data_callback = seek_data
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
        if not self._appsrc:
            return False
        return self._appsrc.emit('push-buffer', buffer_) == gst.FLOW_OK

    def emit_end_of_stream(self):
        """
        Put an end-of-stream token on the playbin. This is typically used in
        combination with :meth:`emit_data`.

        We will get a GStreamer message when the stream playback reaches the
        token, and can then do any end-of-stream related tasks.
        """
        self._playbin.get_property('source').emit('end-of-stream')

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
        return self._playbin.seek_simple(
            gst.Format(gst.FORMAT_TIME), gst.SEEK_FLAG_FLUSH, gst_position)

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
        if result == gst.STATE_CHANGE_FAILURE:
            logger.warning(
                'Setting GStreamer state to %s failed', state.value_name)
            return False
        elif result == gst.STATE_CHANGE_ASYNC:
            logger.debug(
                'Setting GStreamer state to %s is async', state.value_name)
            return True
        else:
            logger.debug(
                'Setting GStreamer state to %s is OK', state.value_name)
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
