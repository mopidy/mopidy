.. _debian-install:

*************
Debian/Ubuntu
*************

If you run a Debian based Linux distribution, like Ubuntu or Raspbian, the
easiest way to install Mopidy is from the
`Mopidy APT archive <https://apt.mopidy.com/>`_.
When installing from the APT archive, you will automatically get updates to
Mopidy in the same way as you get updates to the rest of your system.

If you're on a Raspberry Pi running Debian or Raspbian, the following
instructions will work for you as well. If you're setting up a Raspberry Pi
from scratch, we have a guide for installing Debian/Raspbian and Mopidy. See
:ref:`raspberrypi-installation`.


Distribution and architecture support
=====================================

The packages in the apt.mopidy.com archive are built for:

- **Debian 10 (Buster)**,
  which also works for Raspbian Buster and Ubuntu 19.10 and newer.

The few packages that are compiled are available for multiple CPU
architectures:

- **amd64**
- **i386**
- **armhf**, compatible with all Raspberry Pi models.

This is just what we currently support, not a promise to continue to support
the same in the future. We *will* drop support for older distributions and
architectures when supporting those stops us from moving forward with the
project.


Install from apt.mopidy.com
===========================

#. Add the archive's GPG key::

       sudo mkdir -p /usr/local/share/keyrings
       sudo wget -q -O /usr/local/share/keyrings/mopidy-archive-keyring.gpg \
         https://apt.mopidy.com/mopidy.gpg

#. Add the APT repo to your package sources::

       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list

#. Install Mopidy and all dependencies::

       sudo apt update
       sudo apt install mopidy

#. Now, you're ready to :ref:`run Mopidy <running>`.


Upgrading
=========

When a new release of Mopidy is out, and you can't wait for your system to
figure it out for itself, run the following to upgrade right away::

    sudo apt update
    sudo apt upgrade


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, you need to install additional packages.

To list all the extensions available from apt.mopidy.com, you can run::

    apt search mopidy

To install one of the listed packages, e.g. ``mopidy-mpd``, simply run::

   sudo apt install mopidy-mpd

If you cannot find the extension you want in the APT search result, you can
install it from PyPI using ``pip`` instead. You need to make sure you have
``pip``, the Python package installer installed::

   sudo apt install python3-pip

Even if Mopidy itself is installed from APT it will correctly detect and use
extensions from PyPI installed globally on your system using::

   sudo python3 -m pip install ...

For a comprehensive index of available Mopidy extensions,
including those not installable from APT,
see the `Mopidy extension registry <https://mopidy.com/ext/>`_.
