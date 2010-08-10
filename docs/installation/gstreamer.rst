**********************
Gstreamer installation
**********************

To use the `Gstreamer <http://gstreamer.freedesktop.org/>`_ backend, you first
need to install Gstreamer and its Python bindings.


Installing Gstreamer on Linux
=============================

Gstreamer is packaged for most popular Linux distributions. If you use
Debian/Ubuntu you can install Gstreamer with Aptitude::

    sudo aptitude install python-gst0.10 gstreamer0.10-plugins-good \
        gstreamer0.10-plugins-ugly


Installing Gstreamer on OS X
============================

To install Gstreamer on OS X using Homebrew::

    brew install gst-python gst-plugins-good gst-plugins-ugly

To install Gstreamer on OS X using MacPorts::

    sudo port install py26-gst-python gstreamer-plugins-good \
        gstreamer-plugins-ugly


Testing the installation
========================

If you now run the ``gst-inspect-0.10`` command (the version number may vary),
you should see a long listing of installed plugins, ending in a summary line::

    $ gst-inspect-0.10
    ... long list of installed plugins ...
    Total count: 218 plugins (1 blacklist entry not shown), 1031 features
