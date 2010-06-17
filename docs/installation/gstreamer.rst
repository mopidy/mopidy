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


Setting up Mopidy to use the Gstreamer backend
==============================================

Currently :mod:`mopidy.backends.despotify` is the default
backend. If you want to use :mod:`mopidy.backends.gstreamer`
instead, add the following to ``~/.mopidy/settings.py``::

    BACKENDS = (u'mopidy.backends.gstreamer.GstreamerBackend',)
