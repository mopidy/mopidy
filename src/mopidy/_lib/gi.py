# pyright: reportMissingModuleSource=false
import logging
import signal
import sys
import textwrap

import gi

try:
    gi.require_version("Gst", "1.0")
    gi.require_version("GstBase", "1.0")
    gi.require_version("GstPbutils", "1.0")
except ValueError:
    print(  # noqa: T201
        textwrap.dedent("""
        ERROR: A GObject-based library was not found.

        Mopidy requires GStreamer to work. GStreamer is a C library with a
        number of dependencies itself, and cannot be installed with the regular
        Python tools like pip.

        Please see https://docs.mopidy.com/en/latest/installation/ for
        instructions on how to install the required dependencies.
        """),
    )
    raise

from gi.repository import GLib, GObject, Gst, GstBase, GstPbutils

logger = logging.getLogger(__name__)

Gst.init([])
GLib.set_prgname("mopidy")
GLib.set_application_name("Mopidy")

REQUIRED_GST_VERSION = (1, 26, 2)
REQUIRED_GST_VERSION_DISPLAY = ".".join(map(str, REQUIRED_GST_VERSION))

if Gst.version() < REQUIRED_GST_VERSION:
    sys.exit(
        f"ERROR: Mopidy requires GStreamer >= {REQUIRED_GST_VERSION_DISPLAY}, "
        f"but found {Gst.version_string()}.",
    )


def create_glib_loop() -> GLib.MainLoop:
    logger.debug("Creating GLib mainloop")
    loop = GLib.MainLoop()
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, _on_sigterm, loop)
    _use_glib_loop_for_dbus()
    return loop


def _on_sigterm(loop: GLib.MainLoop) -> bool:
    logger.info("GLib mainloop got SIGTERM. Exiting...")
    loop.quit()
    return GLib.SOURCE_REMOVE


def _use_glib_loop_for_dbus() -> None:
    try:
        # Make GLib's mainloop the event loop for python-dbus
        import dbus.mainloop.glib  # pyright: ignore[reportMissingImports]  # ty:ignore[unresolved-import]  # noqa: PLC0415

        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    except ImportError:
        pass


__all__ = [
    "GLib",
    "GObject",
    "Gst",
    "GstBase",
    "GstPbutils",
    "create_glib_loop",
    "gi",
]
