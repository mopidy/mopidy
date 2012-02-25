.. _installation:

************
Installation
************

There are several ways to install Mopidy. What way is best depends upon your
setup and whether you want to use stable releases or less stable development
versions.


Requirements
============

.. toctree::
    :hidden:

    gstreamer
    libspotify

If you install Mopidy from the APT archive, as described below, APT will take
care of all the dependencies for you. Otherwise, make sure you got the required
dependencies installed.

- Hard dependencies:

  - Python >= 2.6, < 3

  - Pykka >= 0.12.3::

        sudo pip install -U pykka

  - GStreamer 0.10.x, with Python bindings. See :doc:`gstreamer`.

- Optional dependencies:

  - For Spotify support, you need libspotify and pyspotify. See
    :doc:`libspotify`.

  - To scrobble your played tracks to Last.FM, you need pylast::

        sudo pip install -U pylast

  - To use MPRIS, e.g. for controlling Mopidy from the Ubuntu Sound Menu, you
    need some additional requirements::

        sudo apt-get install python-dbus python-indicate

  - Some custom mixers (but not the default one) require additional
    dependencies. See the docs for each mixer.


Install latest stable release
=============================


From APT archive
----------------

If you run a Debian based Linux distribution, like Ubuntu, the easiest way to
install Mopidy is from the Mopidy APT archive. When installing from the APT
archive, you will automatically get updates to Mopidy in the same way as you
get updates to the rest of your distribution.

#. Add the archive's GPG key::

       wget -q -O - http://apt.mopidy.com/mopidy.gpg | sudo apt-key add -

#. Add the following to ``/etc/apt/sources.list``, or if you have the directory
   ``/etc/apt/sources.list.d/``, add it to a file called ``mopidy.list`` in
   that directory::

       # Mopidy APT archive
       deb http://apt.mopidy.com/ stable main contrib non-free
       deb-src http://apt.mopidy.com/ stable main contrib non-free

#. Install Mopidy and all dependencies::

       sudo apt-get update
       sudo apt-get install mopidy

#. Next, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.

When a new release is out, and you can't wait for you system to figure it out
for itself, run the following to force an upgrade::

    sudo apt-get update
    sudo apt-get dist-upgrade


From PyPI using Pip
-------------------

If you are on OS X or on Linux, but can't install from the APT archive, you can
install Mopidy from PyPI using Pip.

#. When you install using Pip, you first need to ensure that all of Mopidy's
   dependencies have been installed. See the section on dependencies above.

#. Then, you need to install Pip::

       sudo apt-get install python-setuptools python-pip   # On Ubuntu/Debian
       sudo easy_install pip                               # On OS X

#. To install the currently latest stable release of Mopidy::

       sudo pip install -U Mopidy

   To upgrade Mopidy to future releases, just rerun this command.

#. Next, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.


Install development version
===========================

If you want to follow the development of Mopidy closer, you may install a
development version of Mopidy. These are not as stable as the releases, but
you'll get access to new features earlier and may help us by reporting issues.


From snapshot using Pip
-----------------------

If you want to follow Mopidy development closer, you may install a snapshot of
Mopidy's ``develop`` branch.

#. When you install using Pip, you first need to ensure that all of Mopidy's
   dependencies have been installed. See the section on dependencies above.

#. Then, you need to install Pip::

       sudo apt-get install python-setuptools python-pip   # On Ubuntu/Debian
       sudo easy_install pip                               # On OS X

#. To install the latest snapshot of Mopidy, run::

       sudo pip install mopidy==dev

   To upgrade Mopidy to future releases, just rerun this command.

#. Next, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.


From Git
--------

If you want to contribute to Mopidy, you should install Mopidy using Git.

#. When you install from Git, you first need to ensure that all of Mopidy's
   dependencies have been installed. See the section on dependencies above.

#. Then install Git, if haven't already::

      sudo apt-get install git-core      # On Ubuntu/Debian
      sudo brew install git               # On OS X using Homebrew

#. Clone the official Mopidy repository, or your own fork of it::

      git clone git://github.com/mopidy/mopidy.git

#. Next, you need to set a couple of :doc:`settings </settings>`.

#. You can then run Mopidy directly from the Git repository::

    cd mopidy/          # Move into the Git repo dir
    python mopidy       # Run python on the mopidy source code dir

#. Later, to get the latest changes to Mopidy::

    cd mopidy/
    git pull

For an introduction to ``git``, please visit `git-scm.com
<http://git-scm.com/>`_. Also, please read our :doc:`developer documentation
</development/index>`.


From AUR on ArchLinux
---------------------

If you are running ArchLinux, you can install a development snapshot of Mopidy
using the package found at http://aur.archlinux.org/packages.php?ID=44026.

#. First, you should consider installing any optional dependencies not included
   by the AUR package, like required for e.g. Last.fm scrobbling.

#. To install Mopidy with GStreamer, libspotify and pyspotify, you can use
   ``packer``, ``yaourt``, or do it by hand like this::

       wget http://aur.archlinux.org/packages/mopidy-git/mopidy-git.tar.gz
       tar xf mopidy-git.tar.gz
       cd mopidy-git/
       makepkg -si

   To upgrade Mopidy to future releases, just rerun ``makepkg``.

#. Next, you need to set a couple of :doc:`settings </settings>`, and then
   you're ready to :doc:`run Mopidy </running>`.
