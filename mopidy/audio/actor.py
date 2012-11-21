from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst
import gobject

import logging

import pykka

from mopidy import settings
from mopidy.utils import process

from . import mixers
from .constants import PlaybackState
from .listener import AudioListener

logger = logging.getLogger('mopidy.audio')

mixers.register_mixers()


class Audio(pykka.ThreadingActor):
    """
    Audio output through `GStreamer <http://gstreamer.freedesktop.org/>`_.

    **Settings:**

    - :attr:`mopidy.settings.OUTPUT`
    - :attr:`mopidy.settings.MIXER`
    - :attr:`mopidy.settings.MIXER_TRACK`
    """

    #: The GStreamer state mapped to :class:`mopidy.audio.PlaybackState`
    state = PlaybackState.STOPPED

    def __init__(self):
        super(Audio, self).__init__()

        self._playbin = None
        self._mixer = None
        self._mixer_track = None
        self._software_mixing = False
        self._appsrc = None

        self._notify_source_signal_id = None
        self._about_to_finish_id = None
        self._message_signal_id = None

    def on_start(self):
        try:
            self._setup_playbin()
            self._setup_output()
            self._setup_mixer()
            self._setup_message_processor()
        except gobject.GError as ex:
            logger.exception(ex)
            process.exit_process()

    def on_stop(self):
        self._teardown_message_processor()
        self._teardown_mixer()
        self._teardown_playbin()

    def _setup_playbin(self):
        self._playbin = gst.element_factory_make('playbin2')

        fakesink = gst.element_factory_make('fakesink')
        self._playbin.set_property('video-sink', fakesink)

        self._about_to_finish_id = self._playbin.connect(
            'about-to-finish', self._on_about_to_finish)
        self._notify_source_signal_id = self._playbin.connect(
            'notify::source', self._on_new_source)

    def _on_about_to_finish(self, element):
        self._appsrc = None

    def _on_new_source(self, element, pad):
        uri = element.get_property('uri')
        if not uri or not uri.startswith('appsrc://'):
            return

        # These caps matches the audio data provided by libspotify
        default_caps = gst.Caps(
            b'audio/x-raw-int, endianness=(int)1234, channels=(int)2, '
            b'width=(int)16, depth=(int)16, signed=(boolean)true, '
            b'rate=(int)44100')
        source = element.get_property('source')
        source.set_property('caps', default_caps)
        # GStreamer does not like unicode
        source.set_property('format', b'time')

        self._appsrc = source

    def _teardown_playbin(self):
        if self._about_to_finish_id:
            self._playbin.disconnect(self._about_to_finish_id)
        if self._notify_source_signal_id:
            self._playbin.disconnect(self._notify_source_signal_id)
        self._playbin.set_state(gst.STATE_NULL)

    def _setup_output(self):
        try:
            output = gst.parse_bin_from_description(
                settings.OUTPUT, ghost_unconnected_pads=True)
            self._playbin.set_property('audio-sink', output)
            logger.info('Audio output set to "%s"', settings.OUTPUT)
        except gobject.GError as ex:
            logger.error(
                'Failed to create audio output "%s": %s', settings.OUTPUT, ex)
            process.exit_process()

    def _setup_mixer(self):
        if not settings.MIXER:
            logger.info('Not setting up audio mixer')
            return

        if settings.MIXER == 'software':
            self._software_mixing = True
            logger.info('Audio mixer is using software mixing')
            return

        try:
            mixerbin = gst.parse_bin_from_description(
                settings.MIXER, ghost_unconnected_pads=False)
        except gobject.GError as ex:
            logger.warning(
                'Failed to create audio mixer "%s": %s', settings.MIXER, ex)
            return

        # We assume that the bin will contain a single mixer.
        mixer = mixerbin.get_by_interface(b'GstMixer')
        if not mixer:
            logger.warning(
                'Did not find any audio mixers in "%s"', settings.MIXER)
            return

        if mixerbin.set_state(gst.STATE_READY) != gst.STATE_CHANGE_SUCCESS:
            logger.warning(
                'Setting audio mixer "%s" to READY failed', settings.MIXER)
            return

        track = self._select_mixer_track(mixer, settings.MIXER_TRACK)
        if not track:
            logger.warning('Could not find usable audio mixer track')
            return

        self._mixer = mixer
        self._mixer_track = track
        logger.info(
            'Audio mixer set to "%s" using track "%s"',
            mixer.get_factory().get_name(), track.label)

    def _select_mixer_track(self, mixer, track_label):
        # Look for track with label == MIXER_TRACK, otherwise fallback to
        # master track which is also an output.
        for track in mixer.list_tracks():
            if track_label:
                if track.label == track_label:
                    return track
            elif track.flags & (gst.interfaces.MIXER_TRACK_MASTER |
                                gst.interfaces.MIXER_TRACK_OUTPUT):
                return track

    def _teardown_mixer(self):
        if self._mixer is not None:
            self._mixer.set_state(gst.STATE_NULL)

    def _setup_message_processor(self):
        bus = self._playbin.get_bus()
        bus.add_signal_watch()
        self._message_signal_id = bus.connect('message', self._on_message)

    def _teardown_message_processor(self):
        if self._message_signal_id:
            bus = self._playbin.get_bus()
            bus.disconnect(self._message_signal_id)
            bus.remove_signal_watch()

    def _on_message(self, bus, message):
        if (message.type == gst.MESSAGE_STATE_CHANGED
                and message.src == self._playbin):
            old_state, new_state, pending_state = message.parse_state_changed()
            self._on_playbin_state_changed(old_state, new_state, pending_state)
        elif message.type == gst.MESSAGE_EOS:
            self._on_end_of_stream()
        elif message.type == gst.MESSAGE_ERROR:
            error, debug = message.parse_error()
            logger.error('%s %s', error, debug)
            self.stop_playback()
        elif message.type == gst.MESSAGE_WARNING:
            error, debug = message.parse_warning()
            logger.warning('%s %s', error, debug)

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
        if self._playbin.get_state()[1] == gst.STATE_NULL:
            return 0
        try:
            position = self._playbin.query_position(gst.FORMAT_TIME)[0]
            return position // gst.MSECOND
        except gst.QueryError, e:
            logger.error('time_position failed: %s', e)
            return 0

    def set_position(self, position):
        """
        Set position in milliseconds.

        :param position: the position in milliseconds
        :type position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self._playbin.get_state()  # block until state changes are done
        handeled = self._playbin.seek_simple(
            gst.Format(gst.FORMAT_TIME), gst.SEEK_FLAG_FLUSH,
            position * gst.MSECOND)
        self._playbin.get_state()  # block until seek is done
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

        new_scale = (0, 100)
        old_scale = (
            self._mixer_track.min_volume, self._mixer_track.max_volume)
        return self._rescale(avg_volume, old=old_scale, new=new_scale)

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

        old_scale = (0, 100)
        new_scale = (
            self._mixer_track.min_volume, self._mixer_track.max_volume)

        volume = self._rescale(volume, old=old_scale, new=new_scale)

        volumes = (volume,) * self._mixer_track.num_channels
        self._mixer.set_volume(self._mixer_track, volumes)

        return self._mixer.get_volume(self._mixer_track) == volumes

    def _rescale(self, value, old=None, new=None):
        """Convert value between scales."""
        new_min, new_max = new
        old_min, old_max = old
        scaling = float(new_max - new_min) / (old_max - old_min)
        return int(round(scaling * (value - old_min) + new_min))

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
