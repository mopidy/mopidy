from __future__ import unicode_literals

import pykka


class CoreListener(object):
    """
    Marker interface for recipients of events sent by the core actor.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the core actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event, **kwargs):
        """Helper to allow calling of core listener events"""
        listeners = pykka.ActorRegistry.get_by_class(CoreListener)
        for listener in listeners:
            listener.proxy().on_event(event, **kwargs)

    def on_event(self, event, **kwargs):
        """
        Called on all events.

        *MAY* be implemented by actor. By default, this method forwards the
        event to the specific event methods.

        :param event: the event name
        :type event: string
        :param kwargs: any other arguments to the specific event handlers
        """
        getattr(self, event)(**kwargs)

    def track_playback_paused(self, tl_track, time_position):
        """
        Called whenever track playback is paused.

        *MAY* be implemented by actor.

        :param tl_track: the track that was playing when playback paused
        :type tl_track: :class:`mopidy.models.TlTrack`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass

    def track_playback_resumed(self, tl_track, time_position):
        """
        Called whenever track playback is resumed.

        *MAY* be implemented by actor.

        :param tl_track: the track that was playing when playback resumed
        :type tl_track: :class:`mopidy.models.TlTrack`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass

    def track_playback_started(self, tl_track):
        """
        Called whenever a new track starts playing.

        *MAY* be implemented by actor.

        :param tl_track: the track that just started playing
        :type tl_track: :class:`mopidy.models.TlTrack`
        """
        pass

    def track_playback_ended(self, tl_track, time_position):
        """
        Called whenever playback of a track ends.

        *MAY* be implemented by actor.

        :param tl_track: the track that was played before playback stopped
        :type tl_track: :class:`mopidy.models.TlTrack`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass

    def playback_state_changed(self, old_state, new_state):
        """
        Called whenever playback state is changed.

        *MAY* be implemented by actor.

        :param old_state: the state before the change
        :type old_state: string from :class:`mopidy.core.PlaybackState` field
        :param new_state: the state after the change
        :type new_state: string from :class:`mopidy.core.PlaybackState` field
        """
        pass

    def tracklist_changed(self):
        """
        Called whenever the tracklist is changed.

        *MAY* be implemented by actor.
        """
        pass

    def playlists_loaded(self):
        """
        Called when playlists are loaded or refreshed.

        *MAY* be implemented by actor.
        """
        pass

    def playlist_changed(self, playlist):
        """
        Called whenever a playlist is changed.

        *MAY* be implemented by actor.

        :param playlist: the changed playlist
        :type playlist: :class:`mopidy.models.Playlist`
        """
        pass

    def options_changed(self):
        """
        Called whenever an option is changed.

        *MAY* be implemented by actor.
        """
        pass

    def volume_changed(self, volume):
        """
        Called whenever the volume is changed.

        *MAY* be implemented by actor.

        :param volume: the new volume in the range [0..100]
        :type volume: int
        """
        pass

    def mute_changed(self, mute):
        """
        Called whenever the mute state is changed.

        *MAY* be implemented by actor.

        :param mute: the new mute state
        :type mute: boolean
        """
        pass

    def seeked(self, time_position):
        """
        Called whenever the time position changes by an unexpected amount, e.g.
        at seek to a new time position.

        *MAY* be implemented by actor.

        :param time_position: the position that was seeked to in milliseconds
        :type time_position: int
        """
        pass
