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

.. note::

   The packages should work with:

   - Debian stable and testing,
   - Raspbian stable and testing,
   - Ubuntu 14.04 LTS and later.

   Some of the packages, including the core "mopidy" packages, does *not* work
   on Ubuntu 12.04 LTS.

   This is just what we currently support, not a promise to continue to
   support the same in the future. We *will* drop support for older
   distributions when supporting those stops us from moving forward with the
   project.

#. Add the archive's GPG key::

       wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -

#. Add the following to ``/etc/apt/sources.list``, or if you have the directory
   ``/etc/apt/sources.list.d/``, add it to a file called ``mopidy.list`` in
   that directory::

       # Mopidy APT archive
       deb http://apt.mopidy.com/ stable main contrib non-free
       deb-src http://apt.mopidy.com/ stable main contrib non-free

   For the lazy, you can simply run the following command to create
   ``/etc/apt/sources.list.d/mopidy.list``::

       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/mopidy.list

#. Install Mopidy and all dependencies::

       sudo apt-get update
       sudo apt-get install mopidy

#. Optional: If you want to use any Mopidy extensions, like Spotify support or
   Last.fm scrobbling, you need to install additional packages.

   To list all the extensions available from apt.mopidy.com, you can run::

       apt-cache search mopidy

   To install one of the listed packages, e.g. ``mopidy-spotify``, simply run::

       sudo apt-get install mopidy-spotify

   For a full list of available Mopidy extensions, including those not
   installable from apt.mopidy.com, see :ref:`ext`.

#. Before continuing, make sure you've read the :ref:`debian` section to learn
   about the differences between running Mopidy as a system service and
   manually as your own system user.

#. Finally, you need to set a couple of :doc:`config values </config>`, and then
   you're ready to :doc:`run Mopidy </running>`.

When a new release of Mopidy is out, and you can't wait for you system to
figure it out for itself, run the following to upgrade right away::

    sudo apt-get update
    sudo apt-get dist-upgrade
