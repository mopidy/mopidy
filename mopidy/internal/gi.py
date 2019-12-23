import sys
import textwrap

try:
    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, GObject, Gst
except ImportError:
    print(
        textwrap.dedent(
            """
        ERROR: A GObject based library was not found.

        Mopidy requires GStreamer to work. GStreamer is a C library with a
        number of dependencies itself, and cannot be installed with the regular
        Python tools like pip.

        Please see https://docs.mopidy.com/en/latest/installation/ for
        instructions on how to install the required dependencies.
    """
        )
    )
    raise
else:
    Gst.init([])
    gi.require_version("GstPbutils", "1.0")
    from gi.repository import GstPbutils

GLib.set_prgname("mopidy")
GLib.set_application_name("Mopidy")

REQUIRED_GST_VERSION = (1, 14, 0)
REQUIRED_GST_VERSION_DISPLAY = ".".join(map(str, REQUIRED_GST_VERSION))

if Gst.version() < REQUIRED_GST_VERSION:
    sys.exit(
        f"ERROR: Mopidy requires GStreamer >= {REQUIRED_GST_VERSION_DISPLAY}, "
        f"but found {Gst.version_string()}."
    )


__all__ = [
    "GLib",
    "GObject",
    "Gst",
    "GstPbutils",
    "gi",
]
