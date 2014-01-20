.. _installation:

************
Installation
************

There are several ways to install Mopidy. What way is best depends upon your OS
and/or distribution. If you want to contribute to the development of Mopidy,
you should first read this page, then have a look at :ref:`run-from-git`.

.. contents:: Installation guides
    :local:


Debian/Ubuntu: Install from apt.mopidy.com
==========================================

If you run a Debian based Linux distribution, like Ubuntu, the easiest way to
install Mopidy is from the `Mopidy APT archive <http://apt.mopidy.com/>`_. When
installing from the APT archive, you will automatically get updates to Mopidy
in the same way as you get updates to the rest of your distribution.

#. Add the archive's GPG key::

       wget -q -O - http://apt.mopidy.com/mopidy.gpg | sudo apt-key add -

#. Add the following to ``/etc/apt/sources.list``, or if you have the directory
   ``/etc/apt/sources.list.d/``, add it to a file called ``mopidy.list`` in
   that directory::

       # Mopidy APT archive
       deb http://apt.mopidy.com/ stable main contrib non-free
       deb-src http://apt.mopidy.com/ stable main contrib non-free

   For the lazy, you can simply run the following command to create
   ``/etc/apt/sources.list.d/mopidy.list``::

       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list http://apt.mopidy.com/mopidy.list

#. Install Mopidy and all dependencies::

       sudo apt-get update
       sudo apt-get install mopidy

   Note that this will only install the main Mopidy package. For e.g. Spotify
   or SoundCloud support you need to install the respective extension packages.
   To list all the extensions available from apt.mopidy.com, you can run::

       apt-cache search mopidy

   To install one of the listed packages, e.g. ``mopidy-spotify``, simply run::

       sudo apt-get install mopidy-spotify

   For a full list of available Mopidy extensions, including those not
   installable from apt.mopidy.com, see :ref:`ext`.

#. Finally, you need to set a couple of :doc:`config values </config>`, and then
   you're ready to :doc:`run Mopidy </running>`.

When a new release of Mopidy is out, and you can't wait for you system to
figure it out for itself, run the following to upgrade right away::

    sudo apt-get update
    sudo apt-get dist-upgrade


Raspberry Pi running Debian
---------------------------

Fred Hatfull has created a guide for installing a Raspberry Pi from scratch
with Debian and Mopidy. See :ref:`raspberrypi-installation`.


Vagrant virtual machine running Ubuntu
--------------------------------------

Paul Sturgess has created a Vagrant and Chef setup that automatically creates
and sets up a virtual machine which runs Mopidy. Check out
https://github.com/paulsturgess/mopidy-vagrant if you're interested in trying
it out.


Arch Linux: Install from AUR
============================

If you are running Arch Linux, you can install Mopidy
using the `mopidy <https://aur.archlinux.org/packages/mopidy/>`_
package found in AUR.

#. To install Mopidy with all dependencies, you can use
   for example `yaourt <https://wiki.archlinux.org/index.php/yaourt>`_::

       yaourt -S mopidy

   To upgrade Mopidy to future releases, just upgrade your system using::

       yaourt -Syu

#. Optional: If you want to use any Mopidy extensions, like Spotify support or
   Last.fm scrobbling, AUR also got `packages for several Mopidy extensions
   <https://aur.archlinux.org/packages/?K=mopidy>`_.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.


OS X: Install from Homebrew and pip
===================================

If you are running OS X, you can install everything needed with Homebrew and
pip.

#. Install `Homebrew <https://github.com/mxcl/homebrew>`_.

   If you are already using Homebrew, make sure your installation is up to
   date before you continue::

       brew update
       brew upgrade

#. Mopidy requires GStreamer 0.10, but Homebrew's main formula repo has
   upgraded its GStreamer packages to 1.0. Thus, you'll need to add an
   alternative formula repo (aka "tap") that has the old GStreamer formulas::

       brew tap homebrew/versions

#. Install the required packages from Homebrew::

       brew install gst-python010 gst-plugins-good010 gst-plugins-ugly010

#. Make sure to include Homebrew's Python ``site-packages`` directory in your
   ``PYTHONPATH``. If you don't include this, Mopidy will not find GStreamer
   and it will crash.

   You can either amend your ``PYTHONPATH`` permanently, by adding the
   following statement to your shell's init file, e.g. ``~/.bashrc``::

       export PYTHONPATH=$(brew --prefix)/lib/python2.7/site-packages:$PYTHONPATH

   Or, you can prefix the Mopidy command every time you run it::

       PYTHONPATH=$(brew --prefix)/lib/python2.7/site-packages mopidy

#. Next up, you need to install some Python packages. To do so, we use pip. If
   you don't have the ``pip`` command, you can install it now::

       sudo easy_install pip

#. Then, install the latest release of Mopidy using pip::

       sudo pip install -U mopidy

#. Optionally, install additional extensions to Mopidy.

   For HTTP frontend support, so you can run Mopidy web clients::

       sudo pip install -U mopidy[http]

   For playing music from Spotify::

       brew install libspotify
       sudo pip install -U mopidy-spotify

   For scrobbling to Last.fm::

       sudo pip install -U mopidy-scrobbler

   For more extensions, see :ref:`ext`.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.


Otherwise: Install from source using pip
========================================

If you are on on Linux, but can't install from the APT archive or from AUR, you
can install Mopidy from PyPI using pip.

#. First of all, you need Python 2.7. Check if you have Python and what
   version by running::

       python --version

#. When you install using pip, you need to make sure you have pip. You'll also
   need a C compiler and the Python development headers to build pyspotify
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

       sudo pip install mopidy==dev

#. Optional: If you want to use the HTTP frontend and web clients, you need
   some additional dependencies::

      sudo pip install -U mopidy[http]

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

          su -c 'echo "/usr/local/lib" > /etc/ld.so.conf.d/libspotify.conf'
          sudo ldconfig

   #. Then install the latest release of Mopidy-Spotify using pip::

          sudo pip install -U mopidy-spotify

#. Optional: If you want to scrobble your played tracks to Last.fm, you need
   to install Mopidy-Scrobbler::

      sudo pip install -U mopidy-scrobbler

#. Optional: To use Mopidy-MPRIS, e.g. for controlling Mopidy from the Ubuntu
   Sound Menu or from an UPnP client via Rygel, you need some additional
   dependencies and the Mopidy-MPRIS extension.

   #. Install the Python bindings for libindicate, and the Python bindings for
      libdbus, the reference D-Bus library.

      On Debian/Ubuntu::

          sudo apt-get install python-dbus python-indicate

   #. Then install the latest release of Mopidy-MPRIS using pip::

          sudo pip install -U mopidy-mpris

#. For more Mopidy extensions, see :ref:`ext`.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.
