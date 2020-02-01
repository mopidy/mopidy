.. _source-install:

*****************
Install from PyPI
*****************

If you are on Linux, but can't install
:ref:`from the APT archive <debian-install>` or
:ref:`from the Arch Linux repository <arch-install>`,
you can install Mopidy from PyPI using the ``pip`` installer.

If you are looking to contribute or wish to install from source using ``git``
please see :ref:`contributing`.

#. First of all, you need Python 3.7 or newer. Check if you have Python and
   what version by running::

       python3 --version

#. You need to make sure you have ``pip``, the Python package installer. You'll
   also need a C compiler and the Python development headers to install some
   Mopidy extensions, like Mopidy-Spotify.

   This is how you install it on Debian/Ubuntu::

       sudo apt install build-essential python3-dev python3-pip

   And on Arch Linux from the official repository::

       sudo pacman -S base-devel python-pip

   And on Fedora Linux from the official repositories::

       sudo dnf install -y gcc python3-devel python3-pip

#. Then you'll need to install GStreamer >= 1.14.0, with Python bindings.
   GStreamer is packaged for most popular Linux distributions. Search for
   GStreamer in your package manager, and make sure to install the Python
   bindings, and the "good" and "ugly" plugin sets.

   **Debian/Ubuntu**

   If you use Debian/Ubuntu you can install GStreamer like this::

       sudo apt install \
           python3-gst-1.0 \
           gir1.2-gstreamer-1.0 \
           gir1.2-gst-plugins-base-1.0 \
           gstreamer1.0-plugins-good \
           gstreamer1.0-plugins-ugly \
           gstreamer1.0-tools

   **Arch Linux**

   If you use Arch Linux, install the following packages from the official
   repository::

       sudo pacman -S \
           gst-python \
           gst-plugins-good \
           gst-plugins-ugly

   **Fedora**

   If you use Fedora you can install GStreamer like this::

       sudo dnf install -y \
           python3-gstreamer1 \
           gstreamer1-plugins-good \
           gstreamer1-plugins-ugly-free

   **Gentoo**

   If you use Gentoo you can install GStreamer like this::

       emerge -av gst-python gst-plugins-meta

   ``gst-plugins-meta`` is the one that actually pulls in the plugins you want,
   so pay attention to the USE flags, e.g. ``alsa``, ``mp3``, etc.

   **macOS**

   If you use macOS, you can install GStreamer from Homebrew::

       brew install \
           gst-python \
           gst-plugins-base \
           gst-plugins-good \
           gst-plugins-ugly

#. Install the latest release of Mopidy::

       sudo python3 -m pip install --upgrade mopidy

   This will use ``pip`` to install the latest release of `Mopidy from PyPI
   <https://pypi.org/project/Mopidy>`_. To upgrade Mopidy to future
   releases, just rerun this command.

#. Now, you're ready to :ref:`run Mopidy <running>`.


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, you need to install additional Mopidy extensions.

You can install any Mopidy extension directly from PyPI with ``pip``. To list
all the extensions available from PyPI, run::

    python3 -m pip search mopidy

To install one of the listed packages, e.g. ``Mopidy-MPD``, simply run::

   sudo python3 -m pip install Mopidy-MPD

Note that extensions installed with ``pip`` will only install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.

For a comprehensive index of available Mopidy extensions,
see the `Mopidy extension registry <https://mopidy.com/ext/>`_.
