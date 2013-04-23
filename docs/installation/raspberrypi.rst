.. _raspberrypi-installation:

****************************
Installation on Raspberry Pi
****************************

As of early August, 2012, running Mopidy on a `Raspberry Pi
<http://www.raspberrypi.org/>`_ is possible, although there are a few
significant drawbacks to doing so. This document is intended to help you get
Mopidy running on your Raspberry Pi and to document the progress made and
issues surrounding running Mopidy on the Raspberry Pi.

As of January 2013, Mopidy will run with Spotify support on both the armel
(soft-float) and armhf (hard-float) architectures, which includes the Raspbian
distribution.

.. image:: /_static/raspberry-pi-by-jwrodgers.jpg
    :width: 640
    :height: 427


.. _raspi-wheezy:

How to for Debian 7 (Wheezy)
============================

#. Download the latest wheezy disk image from
   http://downloads.raspberrypi.org/images/debian/7/. I used the one dated
   2012-08-08.

#. Flash the OS image to your SD card. See
   http://elinux.org/RPi_Easy_SD_Card_Setup for help.

#. If you have an SD card that's >2 GB, you don't have to resize the file
   systems on another computer. Just boot up your Raspberry Pi with the
   unaltered partions, and it will boot right into the ``raspi-config`` tool,
   which will let you grow the root file system to fill the SD card. This tool
   will also allow you do other useful stuff, like turning on the SSH server.

#. You can login to the default user using username ``pi`` and password
   ``raspberry``. To become root, just enter ``sudo -i``.

#. To avoid a couple of potential problems with Mopidy, turn on IPv6 support:

   - Load the IPv6 kernel module now::

         sudo modprobe ipv6

   - Add ``ipv6`` to ``/etc/modules`` to ensure the IPv6 kernel module is
     loaded on boot::

         echo ipv6 | sudo tee -a /etc/modules

#. Installing Mopidy and its dependencies from `apt.mopidy.com
   <http://apt.mopidy.com/>`_, as described in :ref:`installation`. In short::

       wget -q -O - http://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list http://apt.mopidy.com/mopidy.list
       sudo apt-get update
       sudo apt-get install mopidy

#. Since I have a HDMI cable connected, but want the sound on the analog sound
   connector, I have to run::

       amixer cset numid=3 1

   to force it to use analog output. ``1`` means analog, ``0`` means auto, and
   is the default, while ``2`` means HDMI. You can test sound output
   independent of Mopidy by running::

       aplay /usr/share/sounds/alsa/Front_Center.wav

   If you hear a voice saying "Front Center", then your sound is working.

   To make the change to analog output stick, you can add the ``amixer``
   command to e.g. ``/etc/rc.local``, which will be executed when the system is
   booting.


Fixing audio quality issues
===========================

As of January 2013, some reports also indicate that pushing the audio through
PulseAudio may help. We hope to, in the future, provide a complete set of
instructions here leading to acceptable analog audio quality.
