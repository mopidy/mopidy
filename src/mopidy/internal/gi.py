# pyright: reportMissingModuleSource=false

import sys
import textwrap

import gi

try:
    gi.require_version("Gst", "1.0")
    gi.require_version("GstPbutils", "1.0")
except ValueError:
    print(  # noqa: T201
        textwrap.dedent(
            """
        ERROR: A GObject based library was not found.

        Mopidy requires GStreamer to work. GStreamer is a C library with a
        number of dependencies itself, and cannot be installed with the regular
        Python tools like pip.

        Please see https://docs.mopidy.com/en/latest/installation/ for
        instructions on how to install the required dependencies.
    """,
        ),
    )
    raise

from gi.repository import GLib, GObject, Gst, GstPbutils

Gst.init([])
GLib.set_prgname("mopidy")
GLib.set_application_name("Mopidy")

REQUIRED_GST_VERSION = (1, 22, 0)
REQUIRED_GST_VERSION_DISPLAY = ".".join(map(str, REQUIRED_GST_VERSION))

if Gst.version() < REQUIRED_GST_VERSION:
    sys.exit(
        f"ERROR: Mopidy requires GStreamer >= {REQUIRED_GST_VERSION_DISPLAY}, "
        f"but found {Gst.version_string()}.",
    )


__all__ = [
    "GLib",
    "GObject",
    "Gst",
    "GstPbutils",
    "gi",
]
