from __future__ import unicode_literals

import pykka


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
        listeners = pykka.ActorRegistry.get_by_class(AudioListener)
        for listener in listeners:
            listener.proxy().on_event(event, **kwargs)

    def on_event(self, event, **kwargs):
        """
        Called on all events.

        *MAY* be implemented by actor. By default, this method forwards the
        event to the specific event methods.

        For a list of what event names to expect, see the names of the other
        methods in :class:`AudioListener`.

        :param event: the event name
        :type event: string
        :param kwargs: any other arguments to the specific event handlers
        """
        getattr(self, event)(**kwargs)

    def reached_end_of_stream(self):
        """
        Called whenever the end of the audio stream is reached.

        *MAY* be implemented by actor.
        """
        pass

    def state_changed(self, old_state, new_state):
        """
        Called after the playback state have changed.

        Will be called for both immediate and async state changes in GStreamer.

        *MAY* be implemented by actor.

        :param old_state: the state before the change
        :type old_state: string from :class:`mopidy.core.PlaybackState` field
        :param new_state: the state after the change
        :type new_state: string from :class:`mopidy.core.PlaybackState` field
        """
        pass
