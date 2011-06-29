class BackendListener(object):
    """
    Marker interface for recipients of events sent by the backend.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the backend. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    def paused_playing(self, track, time_position):
        """
        Called whenever playback is paused.

        *MAY* be implemented by actor.

        :param track: the track that was playing when playback paused
        :type track: :class:`mopidy.models.Track`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass

    def resumed_playing(self, track, time_position):
        """
        Called whenever playback is resumed.

        *MAY* be implemented by actor.

        :param track: the track that was playing when playback resumed
        :type track: :class:`mopidy.models.Track`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass


    def started_playing(self, track):
        """
        Called whenever a new track starts playing.

        *MAY* be implemented by actor.

        :param track: the track that just started playing
        :type track: :class:`mopidy.models.Track`
        """
        pass

    def stopped_playing(self, track, time_position):
        """
        Called whenever playback is stopped.

        *MAY* be implemented by actor.

        :param track: the track that was played before playback stopped
        :type track: :class:`mopidy.models.Track`
        :param time_position: the time position in milliseconds
        :type time_position: int
        """
        pass
