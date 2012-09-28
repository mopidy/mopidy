from pykka.registry import ActorRegistry


class AudioListener(object):
    """
    Marker interface for recipients of events sent by the audio actor.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the core actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event, **kwargs):
        """Helper to allow calling of audio listener events"""
        listeners = ActorRegistry.get_by_class(AudioListener)
        for listener in listeners:
            getattr(listener.proxy(), event)(**kwargs)

    def reached_end_of_stream(self):
        """
        Called whenever the end of the audio stream is reached.

        *MAY* be implemented by actor.
        """
        pass
