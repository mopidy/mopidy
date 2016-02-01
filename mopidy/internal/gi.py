from __future__ import absolute_import, unicode_literals

import textwrap


try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstPbutils', '1.0')
    from gi.repository import GLib, GObject, Gst, GstPbutils
except ImportError:
    print(textwrap.dedent("""
        ERROR: A GObject Python package was not found.

        Mopidy requires GStreamer to work. GStreamer is a C library with a
        number of dependencies itself, and cannot be installed with the regular
        Python tools like pip.

        Please see http://docs.mopidy.com/en/latest/installation/ for
        instructions on how to install the required dependencies.
    """))
    raise
else:
    Gst.is_initialized() or Gst.init()


__all__ = [
    'GLib',
    'GObject',
    'Gst',
    'GstPbutils',
    'gi',
]
