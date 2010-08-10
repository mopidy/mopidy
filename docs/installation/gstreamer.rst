**********************
GStreamer installation
**********************

To use the Mopidy, you first need to install GStreamer and its Python bindings.


Installing GStreamer on Linux
=============================

GStreamer is packaged for most popular Linux distributions. If you use
Debian/Ubuntu you can install GStreamer with Aptitude::

    sudo aptitude install python-gst0.10 gstreamer0.10-plugins-good \
        gstreamer0.10-plugins-ugly


Installing GStreamer on OS X
============================

.. note::

    We have created GStreamer formulas for Homebrew to make the GStreamer
    installation easy for you, but our formulas has not been merged into
    Homebrew's master branch yet. You should either fetch the formula files
    from `Homebrew's issue #1612
    <http://github.com/mxcl/homebrew/issues/issue/1612>`_ yourself, or fall
    back to using MacPorts.

To install GStreamer on OS X using Homebrew::

    brew install gst-python gst-plugins-good gst-plugins-ugly

To install GStreamer on OS X using MacPorts::

    sudo port install py26-gst-python gstreamer-plugins-good \
        gstreamer-plugins-ugly


Testing the installation
========================

If you now run the ``gst-inspect-0.10`` command (the version number may vary),
you should see a long listing of installed plugins, ending in a summary line::

    $ gst-inspect-0.10
    ... long list of installed plugins ...
    Total count: 218 plugins (1 blacklist entry not shown), 1031 features
