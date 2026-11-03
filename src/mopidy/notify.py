from __future__ import annotations

from mopidy.core import CoreListener


class Notifier:
    """Sends a notification to users.

    Make a notifier with source. Then call
    `info()`, `warning()` or `error()` to send a notification.

    Args:
        source: The name of the component sending the notification.

    """

    def __init__(self, source: str) -> None:
        self.source = source

    def info(self, message: str) -> None:
        """Send a notification with level info to the user."""
        CoreListener.send(
            "notification", message=message, source=self.source, level="info"
        )

    def warning(self, message: str) -> None:
        """Send a notification with level warning to the user."""
        CoreListener.send(
            "notification", message=message, source=self.source, level="warning"
        )

    def error(self, message: str) -> None:
        """Send a notification with level error to the user."""
        CoreListener.send(
            "notification", message=message, source=self.source, level="error"
        )
