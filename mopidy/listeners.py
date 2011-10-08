from pykka import registry

class BackendListener(object):
    """
    Marker interface for recipients of events sent by the backend.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the backend. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event, **kwargs):
        """Helper to allow calling of backend listener events"""
        # FIXME this should be updated once Pykka supports non-blocking calls
        # on proxies or some similar solution.
        registry.ActorRegistry.broadcast({
            'command': 'pykka_call',
            'attr_path': (event,),
            'args': [],
            'kwargs': kwargs,
        }, target_class=BackendListener)

    def track_playback_paused(self, track, time_position):
        """
        Called whenever track playback is paused.

        *MAY* be implemented by actor.

        :param track: the track that was playing when playback paused
        :type track: :class:`mopidy.models.Track`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass

    def track_playback_resumed(self, track, time_position):
        """
        Called whenever track playback is resumed.

        *MAY* be implemented by actor.

        :param track: the track that was playing when playback resumed
        :type track: :class:`mopidy.models.Track`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass


    def track_playback_started(self, track):
        """
        Called whenever a new track starts playing.

        *MAY* be implemented by actor.

        :param track: the track that just started playing
        :type track: :class:`mopidy.models.Track`
        """
        pass

    def track_playback_ended(self, track, time_position):
        """
        Called whenever playback of a track ends.

        *MAY* be implemented by actor.

        :param track: the track that was played before playback stopped
        :type track: :class:`mopidy.models.Track`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass

    def playback_state_changed(self):
        """
        Called whenever playback state is changed.

        *MAY* be implemented by actor.
        """
        pass

    def playlist_changed(self):
        """
        Called whenever a playlist is changed.

        *MAY* be implemented by actor.
        """
        pass

    def options_changed(self):
        """
        Called whenever an option is changed.

        *MAY* be implemented by actor.
        """
        pass

    def volume_changed(self):
        """
        Called whenever the volume is changed.

        *MAY* be implemented by actor.
        """
        pass

    def seeked(self):
        """
        Called whenever the time position changes by an unexpected amount, e.g.
        at seek to a new time position.

        *MAY* be implemented by actor.
        """
        pass
