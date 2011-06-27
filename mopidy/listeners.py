class BackendListener(object):
    """
    Marker interface for recipients of events sent by the backend.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the backend. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    def started_playing(self, track):
        """
        Called whenever a new track starts playing.

        *MAY* be implemented by actor.

        :param track: the track that just started playing
        :type track: :class:`mopidy.models.Track`
        """
        pass

    def stopped_playing(self, track, stop_position):
        """
        Called whenever playback is stopped.

        *MAY* be implemented by actor.

        :param track: the track that was played before playback stopped
        :type track: :class:`mopidy.models.Track`
        :param stop_position: the time position when stopped in milliseconds
        :type stop_position: int
        """
        pass
