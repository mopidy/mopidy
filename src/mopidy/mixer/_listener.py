from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mopidy import listener

if TYPE_CHECKING:
    from mopidy.types import Percentage


class MixerListener(listener.Listener):
    """Marker interface for recipients of events sent by the mixer actor.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the mixer actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event: str, **kwargs: Any) -> None:
        """Helper to allow calling of mixer listener events."""
        listener.send(MixerListener, event, **kwargs)

    def volume_changed(self, volume: Percentage) -> None:
        """Called after the volume has changed.

        *MAY* be implemented by actor.

        :param volume: the new volume
        """

    def mute_changed(self, mute: bool) -> None:
        """Called after the mute state has changed.

        *MAY* be implemented by actor.

        :param mute: :class:`True` if muted, :class:`False` if not muted
        :type mute: bool
        """
