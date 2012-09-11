import pygst
pygst.require('0.10')
import gst
import gobject

import logging

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy import settings, utils
from mopidy.backends.base import Backend
from mopidy.utils import process

# Trigger install of gst mixer plugins
from mopidy import mixers

logger = logging.getLogger('mopidy.gstreamer')


class GStreamer(ThreadingActor):
    """
    Audio output through `GStreamer <http://gstreamer.freedesktop.org/>`_.

    **Settings:**

    - :attr:`mopidy.settings.OUTPUT`
    - :attr:`mopidy.settings.MIXER`
    - :attr:`mopidy.settings.MIXER_TRACK`

    """

    def __init__(self):
        super(GStreamer, self).__init__()

        self._default_caps = gst.Caps("""
            audio/x-raw-int,
            endianness=(int)1234,
            channels=(int)2,
            width=(int)16,
            depth=(int)16,
            signed=(boolean)true,
            rate=(int)44100""")

        self._pipeline = None
        self._source = None
        self._uridecodebin = None
        self._output = None
        self._mixer = None

        self._message_processor_set_up = False

    def on_start(self):
        try:
            self._setup_pipeline()
            self._setup_output()
            self._setup_mixer()
            self._setup_message_processor()
        except gobject.GError as ex:
            logger.exception(ex)
            process.exit_process()

    def on_stop(self):
        self._teardown_message_processor()
        self._teardown_mixer()
        self._teardown_pipeline()

    def _setup_pipeline(self):
        # TODO: replace with and input bin so we simply have an input bin we
        # connect to an output bin with a mixer on the side. set_uri on bin?
        description = ' ! '.join([
            'uridecodebin name=uri',
            'audioconvert name=convert',
            'audioresample name=resample',
            'queue name=queue'])

        logger.debug(u'Setting up base GStreamer pipeline: %s', description)

        self._pipeline = gst.parse_launch(description)
        self._uridecodebin = self._pipeline.get_by_name('uri')

        self._uridecodebin.connect('notify::source', self._on_new_source)
        self._uridecodebin.connect('pad-added', self._on_new_pad,
            self._pipeline.get_by_name('queue').get_pad('sink'))

    def _teardown_pipeline(self):
        self._pipeline.set_state(gst.STATE_NULL)

    def _setup_output(self):
        try:
            self._output = gst.parse_bin_from_description(
                settings.OUTPUT, ghost_unconnected_pads=True)
        except gobject.GError as ex:
            logger.error('Failed to create output "%s": %s',
                settings.OUTPUT, ex)
            process.exit_process()
            return

        self._pipeline.add(self._output)
        gst.element_link_many(self._pipeline.get_by_name('queue'),
                              self._output)
        logger.info('Output set to %s', settings.OUTPUT)

    def _setup_mixer(self):
        if not settings.MIXER:
            logger.info('Not setting up mixer.')
            return

        try:
            mixerbin = gst.parse_bin_from_description(settings.MIXER,
                ghost_unconnected_pads=False)
        except gobject.GError as ex:
            logger.warning('Failed to create mixer "%s": %s',
                settings.MIXER, ex)
            return

        # We assume that the bin will contain a single mixer.
        mixer = mixerbin.get_by_interface('GstMixer')
        if not mixer:
            logger.warning('Did not find any mixers in %r', settings.MIXER)
            return

        if mixerbin.set_state(gst.STATE_READY) != gst.STATE_CHANGE_SUCCESS:
            logger.warning('Setting mixer %r to READY failed.', settings.MIXER)
            return

        track = self._select_mixer_track(mixer, settings.MIXER_TRACK)
        if not track:
            logger.warning('Could not find usable mixer track.')
            return

        self._mixer = (mixer, track)
        logger.info('Mixer set to %s using track called %s',
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
            (mixer, track) = self._mixer
            mixer.set_state(gst.STATE_NULL)

    def _setup_message_processor(self):
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_message)
        self._message_processor_set_up = True

    def _teardown_message_processor(self):
        if self._message_processor_set_up:
            bus = self._pipeline.get_bus()
            bus.remove_signal_watch()

    def _on_new_source(self, element, pad):
        self._source = element.get_property('source')
        try:
            self._source.set_property('caps', self._default_caps)
        except TypeError:
            pass

    def _on_new_pad(self, source, pad, target_pad):
        if not pad.is_linked():
            if target_pad.is_linked():
                target_pad.get_peer().unlink(target_pad)
            pad.link(target_pad)

    def _on_message(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            self._notify_backend_of_eos()
        elif message.type == gst.MESSAGE_ERROR:
            error, debug = message.parse_error()
            logger.error(u'%s %s', error, debug)
            self.stop_playback()
        elif message.type == gst.MESSAGE_WARNING:
            error, debug = message.parse_warning()
            logger.warning(u'%s %s', error, debug)

    def _notify_backend_of_eos(self):
        backend_refs = ActorRegistry.get_by_class(Backend)
        assert len(backend_refs) <= 1, 'Expected at most one running backend.'
        if backend_refs:
            logger.debug(u'Notifying backend of end-of-stream.')
            backend_refs[0].proxy().playback.on_end_of_track()
        else:
            logger.debug(u'No backend to notify of end-of-stream found.')

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
        Get volume level of the installed mixer.

           0 == muted.
         100 == max volume for given system.
        None == no mixer present, i.e. volume unknown.

        :rtype: int in range [0..100] or :class:`None`
        """
        if self._mixer is None:
            return None

        mixer, track = self._mixer

        volumes = mixer.get_volume(track)
        avg_volume = float(sum(volumes)) / len(volumes)

        new_scale = (0, 100)
        old_scale = (track.min_volume, track.max_volume)
        return utils.rescale(avg_volume, old=old_scale, new=new_scale)

    def set_volume(self, volume):
        """
        Set volume level of the installed mixer.

        :param volume: the volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        if self._mixer is None:
            return False

        mixer, track = self._mixer

        old_scale = (0, 100)
        new_scale = (track.min_volume, track.max_volume)

        volume = utils.rescale(volume, old=old_scale, new=new_scale)

        volumes = (volume,) * track.num_channels
        mixer.set_volume(track, volumes)

        return mixer.get_volume(track) == volumes

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
