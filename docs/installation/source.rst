.. _source-install:

*******************
Install from source
*******************

If you are on Linux, but can't install :ref:`from the APT archive
<debian-install>` or :ref:`from the Arch Linux repository <arch-install>`, you can install Mopidy
from PyPI using the ``pip`` installer.

If you are looking to contribute or wish to install from source using ``git``
please follow the directions :ref:`here <contributing>`.

#. First of all, you need Python 2.7. Check if you have Python and what
   version by running::

       python --version

#. You need to make sure you have ``pip``, the Python package installer. You'll
   also need a C compiler and the Python development headers to build pyspotify
   later.

   This is how you install it on Debian/Ubuntu::

       sudo apt-get install build-essential python-dev python-pip

   And on Arch Linux from the official repository::

       sudo pacman -S base-devel python2-pip

   And on Fedora Linux from the official repositories::

       sudo yum install -y gcc python-devel python-pip

   .. note::

       On Fedora Linux, you must replace ``pip`` with ``pip-python`` in the
       following steps.

#. Then you'll need to install GStreamer >= 1.2.3, with Python bindings.
   GStreamer is packaged for most popular Linux distributions. Search for
   GStreamer in your package manager, and make sure to install the Python
   bindings, and the "good" and "ugly" plugin sets.

   If you use Debian/Ubuntu you can install GStreamer like this::

       sudo apt-get install python-gst-1.0 \
           gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 \
           gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
           gstreamer1.0-tools

   If you use Arch Linux, install the following packages from the official
   repository::

       sudo pacman -S gst-python2 gst-plugins-good gst-plugins-ugly

   If you use Fedora you can install GStreamer like this::

       sudo yum install -y python-gstreamer1 gstreamer1-plugins-good \
           gstreamer1-plugins-ugly

   If you use Gentoo you can install GStreamer like this::

       emerge -av gst-python gst-plugins-meta

   ``gst-plugins-meta`` is the one that actually pulls in the plugins you want,
   so pay attention to the USE flags, e.g. ``alsa``, ``mp3``, etc.

#. Install the latest release of Mopidy::

       sudo pip install -U mopidy

   This will use ``pip`` to install the latest release of `Mopidy from PyPI
   <https://pypi.python.org/pypi/Mopidy>`_. To upgrade Mopidy to future
   releases, just rerun this command.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, you need to install additional Mopidy extensions.

You can install any Mopidy extension directly from PyPI with ``pip``. To list
all the extensions available from PyPI, run::

    pip search mopidy

Note that extensions installed from PyPI will only automatically install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.

For a full list of available Mopidy extensions see :ref:`ext`.
