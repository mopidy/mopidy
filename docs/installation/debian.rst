.. _debian-install:

******************************************
Debian/Ubuntu: Install from apt.mopidy.com
******************************************

If you run a Debian based Linux distribution, like Ubuntu, the easiest way to
install Mopidy is from the `Mopidy APT archive <https://apt.mopidy.com/>`_.
When installing from the APT archive, you will automatically get updates to
Mopidy in the same way as you get updates to the rest of your system.

If you're on a Raspberry Pi running Debian or Raspbian, the following
instructions should work for you as well. If you're setting up a Raspberry Pi
from scratch, we have a guide for installing Debian/Raspbian and Mopidy. See
:ref:`raspberrypi-installation`.

The packages are built for:

- Debian jessie (stable), which also works for Raspbian jessie and Ubuntu 14.04
  LTS and newer.

The packages are available for multiple CPU architectures: i386, amd64, armel,
and armhf (compatible with Raspberry Pi 1 and 2).

.. note::

   This is just what we currently support, not a promise to continue to
   support the same in the future. We *will* drop support for older
   distributions and architectures when supporting those stops us from moving
   forward with the project.

#. Add the archive's GPG key::

       wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -

#. Add the APT repo to your package sources::

       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list

#. Install Mopidy and all dependencies::

       sudo apt-get update
       sudo apt-get install mopidy

#. Finally, you need to set a couple of :doc:`config values </config>`, and then
   you're ready to :doc:`run Mopidy </running>` or run Mopidy as a
   :ref:`service <service>`.

When a new release of Mopidy is out, and you can't wait for you system to
figure it out for itself, run the following to upgrade right away::

    sudo apt-get update
    sudo apt-get dist-upgrade


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, you need to install additional packages.

To list all the extensions available from apt.mopidy.com, you can run::

    apt-cache search mopidy

To install one of the listed packages, e.g. ``mopidy-spotify``, simply run::

   sudo apt-get install mopidy-spotify

You can also install any Mopidy extension directly from PyPI with ``pip``. To
list all the extensions available from PyPI, run::

    pip search mopidy

Note that extensions installed from PyPI will only automatically install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.

For a full list of available Mopidy extensions, including those not
installable from apt.mopidy.com, see :ref:`ext`.
