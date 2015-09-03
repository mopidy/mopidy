from __future__ import absolute_import, unicode_literals

from mopidy import listener


class AudioListener(listener.Listener):

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
        listener.send(AudioListener, event, **kwargs)

    def reached_end_of_stream(self):
        """
        Called whenever the end of the audio stream is reached.

        *MAY* be implemented by actor.
        """
        pass

    def stream_changed(self, uri):
        """
        Called whenever the audio stream changes.

        *MAY* be implemented by actor.

        :param string uri: URI the stream has started playing.
        """
        pass

    def position_changed(self, position):
        """
        Called whenever the position of the stream changes.

        *MAY* be implemented by actor.

        :param int position: Position in milliseconds.
        """
        pass

    def state_changed(self, old_state, new_state, target_state):
        """
        Called after the playback state have changed.

        Will be called for both immediate and async state changes in GStreamer.

        Target state is used to when we should be in the target state, but
        temporarily need to switch to an other state. A typical example of this
        is buffering. When this happens an event with
        `old=PLAYING, new=PAUSED, target=PLAYING` will be emitted. Once we have
        caught up a `old=PAUSED, new=PLAYING, target=None` event will be
        be generated.

        Regular state changes will not have target state set as they are final
        states which should be stable.

        *MAY* be implemented by actor.

        :param old_state: the state before the change
        :type old_state: string from :class:`mopidy.core.PlaybackState` field
        :param new_state: the state after the change
        :type new_state: A :class:`mopidy.core.PlaybackState` field
        :type new_state: string from :class:`mopidy.core.PlaybackState` field
        :param target_state: the intended state
        :type target_state: string from :class:`mopidy.core.PlaybackState`
            field or :class:`None` if this is a final state.
        """
        pass

    def tags_changed(self, tags):
        """
        Called whenever the current audio stream's tags change.

        This event signals that some track metadata has been updated. This can
        be metadata such as artists, titles, organization, or details about the
        actual audio such as bit-rates, numbers of channels etc.

        For the available tag keys please refer to GStreamer documentation for
        tags.

        *MAY* be implemented by actor.

        :param tags: The tags that have just been updated.
        :type tags: :class:`set` of strings
        """
        pass
