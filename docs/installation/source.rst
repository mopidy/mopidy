.. _source-install:

*******************
Install from source
*******************

If you are on Linux, but can't install :ref:`from the APT archive
<debian-install>` or :ref:`from AUR <arch-install>`, you can install Mopidy
from source by hand.

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

#. Then you'll need to install GStreamer 0.10 (>= 0.10.31, < 0.11), with Python
   bindings. GStreamer is packaged for most popular Linux distributions. Search
   for GStreamer in your package manager, and make sure to install the Python
   bindings, and the "good" and "ugly" plugin sets.

   If you use Debian/Ubuntu you can install GStreamer like this::

       sudo apt-get install python-gst0.10 gstreamer0.10-plugins-good \
           gstreamer0.10-plugins-ugly gstreamer0.10-tools

   If you use Arch Linux, install the following packages from the official
   repository::

       sudo pacman -S gstreamer0.10-python gstreamer0.10-good-plugins \
           gstreamer0.10-ugly-plugins

   If you use Fedora you can install GStreamer like this::

       sudo yum install -y python-gst0.10 gstreamer0.10-plugins-good \
           gstreamer0.10-plugins-ugly gstreamer0.10-tools

   If you use Gentoo you need to be careful because GStreamer 0.10 is in a
   different lower slot than 1.0, the default. Your emerge commands will need
   to include the slot::

       emerge -av gst-python gst-plugins-bad:0.10 gst-plugins-good:0.10 \
           gst-plugins-ugly:0.10 gst-plugins-meta:0.10

   ``gst-plugins-meta:0.10`` is the one that actually pulls in the plugins you
   want, so pay attention to the use flags, e.g. ``alsa``, ``mp3``, etc.

#. Install the latest release of Mopidy::

       sudo pip install -U mopidy

   To upgrade Mopidy to future releases, just rerun this command.

   Alternatively, if you want to track Mopidy development closer, you may
   install a snapshot of Mopidy's ``develop`` Git branch using pip::

       sudo pip install --allow-unverified=mopidy mopidy==dev

#. Optional: If you want Spotify support in Mopidy, you'll need to install
   libspotify and the Mopidy-Spotify extension.

   #. Download and install the latest version of libspotify for your OS and CPU
      architecture from `Spotify
      <https://developer.spotify.com/technologies/libspotify/>`_.

      For libspotify 12.1.51 for 64-bit Linux the process is as follows::

          wget https://developer.spotify.com/download/libspotify/libspotify-12.1.51-Linux-x86_64-release.tar.gz
          tar zxfv libspotify-12.1.51-Linux-x86_64-release.tar.gz
          cd libspotify-12.1.51-Linux-x86_64-release/
          sudo make install prefix=/usr/local

      Remember to adjust the above example for the latest libspotify version
      supported by pyspotify, your OS, and your CPU architecture.

   #. If you're on Fedora, you must add a configuration file so libspotify.so
      can be found::

          echo /usr/local/lib | sudo tee /etc/ld.so.conf.d/libspotify.conf
          sudo ldconfig

   #. Then install the latest release of Mopidy-Spotify using pip::

          sudo pip install -U mopidy-spotify

#. Optional: If you want to scrobble your played tracks to Last.fm, you need
   to install Mopidy-Scrobbler::

      sudo pip install -U mopidy-scrobbler

#. For a full list of available Mopidy extensions, see :ref:`ext`.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.
