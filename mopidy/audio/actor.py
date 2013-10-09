from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst
import gobject

import logging

import pykka

from mopidy.utils import process

from . import mixers, playlists, utils
from .constants import PlaybackState
from .listener import AudioListener

logger = logging.getLogger('mopidy.audio')

mixers.register_mixers()

playlists.register_typefinders()
playlists.register_elements()


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

    def __init__(self, config):
        super(Audio, self).__init__()

        self._config = config

        self._playbin = None
        self._signal_ids = {}  # {(element, event): signal_id}

        self._mixer = None
        self._mixer_track = None
        self._mixer_scale = None
        self._software_mixing = False
        self._volume_set = None

        self._appsrc = None
        self._appsrc_caps = None
        self._appsrc_need_data_callback = None
        self._appsrc_enough_data_callback = None
        self._appsrc_seek_data_callback = None

    def on_start(self):
        try:
            self._setup_playbin()
            self._setup_output()
            self._setup_visualizer()
            self._setup_mixer()
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

        self._connect(playbin, 'about-to-finish', self._on_about_to_finish)
        self._connect(playbin, 'notify::source', self._on_new_source)

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

    def _setup_mixer(self):
        mixer_desc = self._config['audio']['mixer']
        track_desc = self._config['audio']['mixer_track']

        if mixer_desc is None:
            logger.info('Not setting up audio mixer')
            return

        if mixer_desc == 'software':
            self._software_mixing = True
            logger.info('Audio mixer is using software mixing')
            return

        try:
            mixerbin = gst.parse_bin_from_description(
                mixer_desc, ghost_unconnected_pads=False)
        except gobject.GError as ex:
            logger.warning(
                'Failed to create audio mixer "%s": %s', mixer_desc, ex)
            return

        # We assume that the bin will contain a single mixer.
        mixer = mixerbin.get_by_interface(b'GstMixer')
        if not mixer:
            logger.warning(
                'Did not find any audio mixers in "%s"', mixer_desc)
            return

        if mixerbin.set_state(gst.STATE_READY) != gst.STATE_CHANGE_SUCCESS:
            logger.warning(
                'Setting audio mixer "%s" to READY failed', mixer_desc)
            return

        track = self._select_mixer_track(mixer, track_desc)
        if not track:
            logger.warning('Could not find usable audio mixer track')
            return

        self._mixer = mixer
        self._mixer_track = track
        self._mixer_scale = (
            self._mixer_track.min_volume, self._mixer_track.max_volume)
        logger.info(
            'Audio mixer set to "%s" using track "%s"',
            str(mixer.get_factory().get_name()).decode('utf-8'),
            str(track.label).decode('utf-8'))

    def _select_mixer_track(self, mixer, track_label):
        # Ignore tracks without volumes, then look for track with
        # label equal to the audio/mixer_track config value, otherwise fallback
        # to first usable track hoping the mixer gave them to us in a sensible
        # order.

        usable_tracks = []
        for track in mixer.list_tracks():
            if not mixer.get_volume(track):
                continue

            if track_label and track.label == track_label:
                return track
            elif track.flags & (gst.interfaces.MIXER_TRACK_MASTER |
                                gst.interfaces.MIXER_TRACK_OUTPUT):
                usable_tracks.append(track)

        if usable_tracks:
            return usable_tracks[0]

    def _teardown_mixer(self):
        if self._mixer is not None:
            self._mixer.set_state(gst.STATE_NULL)

    def _setup_message_processor(self):
        bus = self._playbin.get_bus()
        bus.add_signal_watch()
        self._connect(bus, 'message', self._on_message)

    def _teardown_message_processor(self):
        bus = self._playbin.get_bus()
        self._disconnect(bus, 'message')
        bus.remove_signal_watch()

    def _on_message(self, bus, message):
        if (message.type == gst.MESSAGE_STATE_CHANGED
                and message.src == self._playbin):
            old_state, new_state, pending_state = message.parse_state_changed()
            self._on_playbin_state_changed(old_state, new_state, pending_state)
        elif message.type == gst.MESSAGE_BUFFERING:
            percent = message.parse_buffering()
            logger.debug('Buffer %d%% full', percent)
        elif message.type == gst.MESSAGE_EOS:
            self._on_end_of_stream()
        elif message.type == gst.MESSAGE_ERROR:
            error, debug = message.parse_error()
            logger.error(
                '%s Debug message: %s',
                str(error).decode('utf-8'), debug.decode('utf-8') or 'None')
            self.stop_playback()
        elif message.type == gst.MESSAGE_WARNING:
            error, debug = message.parse_warning()
            logger.warning(
                '%s Debug message: %s',
                str(error).decode('utf-8'), debug.decode('utf-8') or 'None')

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

        if new_state == gst.STATE_PLAYING:
            new_state = PlaybackState.PLAYING
        elif new_state == gst.STATE_PAUSED:
            new_state = PlaybackState.PAUSED
        elif new_state == gst.STATE_NULL:
            new_state = PlaybackState.STOPPED

        old_state, self.state = self.state, new_state

        logger.debug(
            'Triggering event: state_changed(old_state=%s, new_state=%s)',
            old_state, new_state)
        AudioListener.send(
            'state_changed', old_state=old_state, new_state=new_state)

    def _on_end_of_stream(self):
        logger.debug('Triggering reached_end_of_stream event')
        AudioListener.send('reached_end_of_stream')

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
        Get volume level of the installed mixer.

        Example values:

        0:
            Muted.
        100:
            Max volume for given system.
        :class:`None`:
            No mixer present, so the volume is unknown.

        :rtype: int in range [0..100] or :class:`None`
        """
        if self._software_mixing:
            return int(round(self._playbin.get_property('volume') * 100))

        if self._mixer is None:
            return None

        volumes = self._mixer.get_volume(self._mixer_track)
        avg_volume = float(sum(volumes)) / len(volumes)

        internal_scale = (0, 100)

        if self._volume_set is not None:
            volume_set_on_mixer_scale = self._rescale(
                self._volume_set, old=internal_scale, new=self._mixer_scale)
        else:
            volume_set_on_mixer_scale = None

        if volume_set_on_mixer_scale == avg_volume:
            return self._volume_set
        else:
            return self._rescale(
                avg_volume, old=self._mixer_scale, new=internal_scale)

    def set_volume(self, volume):
        """
        Set volume level of the installed mixer.

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        if self._software_mixing:
            self._playbin.set_property('volume', volume / 100.0)
            return True

        if self._mixer is None:
            return False

        self._volume_set = volume

        internal_scale = (0, 100)

        volume = self._rescale(
            volume, old=internal_scale, new=self._mixer_scale)

        volumes = (volume,) * self._mixer_track.num_channels
        self._mixer.set_volume(self._mixer_track, volumes)

        return self._mixer.get_volume(self._mixer_track) == volumes

    def _rescale(self, value, old=None, new=None):
        """Convert value between scales."""
        new_min, new_max = new
        old_min, old_max = old
        if old_min == old_max:
            return old_max
        scaling = float(new_max - new_min) / (old_max - old_min)
        return int(round(scaling * (value - old_min) + new_min))

    def get_mute(self):
        """
        Get mute status of the installed mixer.

        :rtype: :class:`True` if muted, :class:`False` if unmuted,
          :class:`None` if no mixer is installed.
        """
        if self._software_mixing:
            return self._playbin.get_property('mute')

        if self._mixer_track is None:
            return None

        return bool(self._mixer_track.flags & gst.interfaces.MIXER_TRACK_MUTE)

    def set_mute(self, mute):
        """
        Mute or unmute of the installed mixer.

        :param mute: Wether to mute the mixer or not.
        :type mute: bool
        :rtype: :class:`True` if successful, else :class:`False`
        """
        if self._software_mixing:
            return self._playbin.set_property('mute', bool(mute))

        if self._mixer_track is None:
            return False

        return self._mixer.set_mute(self._mixer_track, bool(mute))

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
