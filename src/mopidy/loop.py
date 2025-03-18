from __future__ import annotations

import logging
import signal
import time

logger = logging.getLogger(__name__)


class DummyLoop:
    def run(self):
        while True:
            time.sleep(60)

    def quit(self):
        pass


try:
    from mopidy.internal.gi import GLib

    class GlibMainLoop(GLib.MainLoop):
        def on_sigterm(self) -> bool:
            logger.info("GLib mainloop got SIGTERM. Exiting...")
            self.quit()
            return GLib.SOURCE_REMOVE

        def __init__(self):
            super().__init__()
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.on_sigterm)
except ImportError:
    GlibMainLoop = None  # type: ignore[reportAssignmentType]


def get_loop_class():
    if GlibMainLoop:
        return GlibMainLoop
    return DummyLoop
