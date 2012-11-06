.. _installation:

*******************
Mopidy installation
*******************

There are several ways to install Mopidy. What way is best depends upon your OS
and/or distribution. If you want to contribute to the development of Mopidy,
you should first read this page, then have a look at :ref:`run-from-git`.


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

#. Finally, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.

When a new release of Mopidy is out, and you can't wait for you system to
figure it out for itself, run the following to upgrade right away::

    sudo apt-get update
    sudo apt-get dist-upgrade


Arch Linux: Install from AUR
============================

If you are running Arch Linux, you can install a development snapshot of Mopidy
using the `mopidy-git <https://aur.archlinux.org/packages/mopidy-git/>`_
package found in AUR.

#. To install Mopidy with GStreamer, libspotify and pyspotify, you can use
   ``packer``, ``yaourt``, or do it by hand like this::

       wget http://aur.archlinux.org/packages/mopidy-git/mopidy-git.tar.gz
       tar xf mopidy-git.tar.gz
       cd mopidy-git/
       makepkg -si

   To upgrade Mopidy to future releases, just rerun ``makepkg``.

#. Optional: If you want to scrobble your played tracks to Last.fm, you need to
   install `python2-pylast
   <https://aur.archlinux.org/packages/python2-pylast/>`_ from AUR.

#. Finally, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.


Otherwise: Install from source using Pip
========================================

If you are on OS X or on Linux, but can't install from the APT archive or from
AUR, you can install Mopidy from PyPI using Pip.

#. First of all, you need Python >= 2.6, < 3. Check if you have Python and what
   version by running::

       python --version

#. When you install using Pip, you need to make sure you have Pip. If you
   don't, this is how you install it on Debian/Ubuntu::

       sudo apt-get install python-setuptools python-pip

   Or on OS X::

       sudo easy_install pip

#. Then you'll need to install all of Mopidy's hard dependencies:

   - Pykka >= 1.0::

         sudo pip install -U pykka

   - GStreamer 0.10.x, with Python bindings. See :doc:`gstreamer` for detailed
     instructions.

#. Optional: If you want Spotify support in Mopidy, you'll need to install
   libspotify and the Python bindings, pyspotify. See :doc:`libspotify` for
   detailed instructions.

#. Optional: If you want to scrobble your played tracks to Last.fm, you need
   pylast::

      sudo pip install -U pylast

#. Optional: To use MPRIS, e.g. for controlling Mopidy from the Ubuntu Sound
   Menu, you need some additional requirements. On Debian/Ubuntu::

      sudo apt-get install python-dbus python-indicate

#. Then, to install the latest release of Mopidy::

       sudo pip install -U mopidy

   To upgrade Mopidy to future releases, just rerun this command.

   Alternatively, if you want to follow Mopidy development closer, you may
   install a snapshot of Mopidy's ``develop`` Git branch using Pip::

        sudo pip install mopidy==dev

#. Finally, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.
