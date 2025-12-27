from __future__ import annotations

from typing import Any

from mopidy import listener


class BackendListener(listener.Listener):
    """Marker interface for recipients of events sent by the backend actors.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in a backend actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.

    Normally, only the Core actor should mix in this class.
    """

    @staticmethod
    def send(event: str, **kwargs: Any) -> None:
        """Helper to allow calling of backend listener events."""
        listener.send(BackendListener, event, **kwargs)

    def playlists_loaded(self) -> None:
        """Called when playlists are loaded or refreshed.

        *MAY* be implemented by actor.
        """
