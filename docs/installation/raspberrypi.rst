.. _raspberrypi-installation:

****************************
Installation on Raspberry Pi
****************************

As of early August, 2012, running Mopidy on a `Raspberry Pi
<http://www.raspberrypi.org/>`_ is possible, although there are a few
significant drawbacks to doing so. This document is intended to help you get
Mopidy running on your Raspberry Pi and to document the progress made and
issues surrounding running Mopidy on the Raspberry Pi.

Mopidy will not currently run with Spotify support on the foundation-provided
`Raspbian <http://www.raspbian.org>`_ distribution. See :ref:`not-raspbian` for
details. However, Mopidy should run with Spotify support on any ARM Debian
image that has hardware floating-point support **disabled**.

.. image:: /_static/raspberry-pi-by-jwrodgers.jpg
    :width: 640
    :height: 427


.. _raspi-squeeze:

How to for Debian 6 (Squeeze)
=============================

The following guide illustrates how to get Mopidy running on a minimal Debian
squeeze distribution.

1. The image used can be downloaded at
   http://www.linuxsystems.it/2012/06/debian-wheezy-raspberry-pi-minimal-image/.
   This image is a very minimal distribution and does not include many common
   packages you might be used to having access to. If you find yourself trying
   to complete instructions here and getting ``command not found``, try using
   ``apt-get`` to install the relevant packages!

2. Flash the OS image to your SD card. See
   http://elinux.org/RPi_Easy_SD_Card_Setup for help.

3. If you have an SD card that's >2 GB, resize the disk image to use some more
   space (we'll need a bit more to install some packages and stuff). See
   http://elinux.org/RPi_Resize_Flash_Partitions#Manually_resizing_the_SD_card_on_Raspberry_Pi
   for help.

4. To even get to the point where we can start installing software let's create
   a new user and give it sudo access.

   - Install ``sudo``::

         apt-get install sudo

   - Create a user account::

         adduser <username>

   - Give the user sudo access by adding it to the ``sudo`` group so we don't
     have to do everything on the ``root`` account::

         adduser <username> sudo

   - While we're at it, give your user access to the sound card by adding it to
     the audio group::

         adduser <username> audio

   - Log in to your Raspberry Pi again with your new user account instead of
     the ``root`` account.

5. Enable the Raspberry Pi's sound drivers:

   - To enable the Raspberry Pi's sound driver::

         sudo modprobe snd_bcm2835

   - To load the sound driver at boot time::

         echo "snd_bcm2835" | sudo tee /etc/modules

6. Let's get the Raspberry Pi up-to-date:

   - Get some tools that we need to download and run the ``rpi-update``
     script::

         sudo apt-get install ca-certificates git-core binutils

   - Download ``rpi-update`` from Github::

         sudo wget https://raw.github.com/Hexxeh/rpi-update/master/rpi-update

   - Move ``rpi-update`` to an appropriate location::

         sudo mv rpi-update /usr/local/bin/rpi-update

   - Make ``rpi-update`` executable::

         sudo chmod +x /usr/local/bin/rpi-update

   - Finally! Update your firmware::

         sudo rpi-update

   - After firmware updating finishes, reboot your Raspberry Pi::

         sudo reboot

7. To avoid a couple of potential problems with Mopidy, turn on IPv6 support:

   - Load the IPv6 kernel module now::

         sudo modprobe ipv6

   - Add ``ipv6`` to ``/etc/modules`` to ensure the IPv6 kernel module is
     loaded on boot::

         echo ipv6 | sudo tee /etc/modules

8. Installing Mopidy and its dependencies from `apt.mopidy.com
   <http://apt.mopidy.com/>`_, as described in :ref:`installation`. In short::

       wget -q -O - http://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list http://apt.mopidy.com/mopidy.list
       sudo apt-get update
       sudo apt-get install mopidy

9. jackd2, which should be installed at this point, seems to cause some
   problems. Let's install jackd1, as it seems to work a little bit better::

       sudo apt-get install jackd1

You may encounter some issues with your audio configuration where sound does
not play. If that happens, edit your ``/etc/asound.conf`` to read something
like::

    pcm.mmap0 {
        type mmap_emul;
        slave {
          pcm "hw:0,0";
        }
    }

    pcm.!default {
      type plug;
      slave {
        pcm mmap0;
      }
    }


.. _raspi-wheezy:

How to for Debian 7 (Wheezy)
============================

This is a very similar system to Debian 6.0 above, but with a bit newer
software packages, as Wheezy is going to be the next release of Debian.

1. Download the latest wheezy disk image from
   http://downloads.raspberrypi.org/images/debian/7/. I used the one dated
   2012-08-08.

2. Flash the OS image to your SD card. See
   http://elinux.org/RPi_Easy_SD_Card_Setup for help.

3. If you have an SD card that's >2 GB, you don't have to resize the file
   systems on another computer. Just boot up your Raspberry Pi with the
   unaltered partions, and it will boot right into the ``raspi-config`` tool,
   which will let you grow the root file system to fill the SD card. This tool
   will also allow you do other useful stuff, like turning on the SSH server.

4. As opposed to on Squeeze, ``sudo`` comes preinstalled. You can login to the
   default user using username ``pi`` and password ``raspberry``. To become
   root, just enter ``sudo -i``.

   Opposed to on Squeeze, there is no need to add your user to the ``audio``
   group, as the ``pi`` user already is a member of that group.

5. As opposed to on Squeeze, the correct sound driver comes preinstalled.

6. As opposed  to on Squeeze, your kernel and GPU firmware is rather up to date
   when running Wheezy.

7. To avoid a couple of potential problems with Mopidy, turn on IPv6 support:

   - Load the IPv6 kernel module now::

         sudo modprobe ipv6

   - Add ``ipv6`` to ``/etc/modules`` to ensure the IPv6 kernel module is
     loaded on boot::

         echo ipv6 | sudo tee /etc/modules

8. Installing Mopidy and its dependencies from `apt.mopidy.com
   <http://apt.mopidy.com/>`_, as described in :ref:`installation`. In short::

       wget -q -O - http://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
       sudo wget -q -O /etc/apt/sources.list.d/mopidy.list http://apt.mopidy.com/mopidy.list
       sudo apt-get update
       sudo apt-get install mopidy

9. Since I have a HDMI cable connected, but want the sound on the analog sound
   connector, I have to run::

       amixer cset numid=3 1

   to force it to use analog output. ``1`` means analog, ``0`` means auto, and
   is the default, while ``2`` means HDMI. You can test sound output
   independent of Mopidy by running::

       aplay /usr/share/sounds/alsa/Front_Center.wav

   To make the change to analog output stick, you can add the ``amixer`` command
   to e.g. ``/etc/rc.local``, which will be executed when the system is
   booting.


Known Issues
============

Audio Quality
-------------

The Raspberry Pi's audio quality can be sub-par through the analog output. This
is known and unlikely to be fixed as including any higher-quality hardware
would increase the cost of the board. If you experience crackling/hissing or
skipping audio, you may want to try a USB sound card. Additionally, you could
lower your default ALSA sampling rate to 22KHz, though this will lead to a
substantial decrease in sound quality.


.. _not-raspbian:

Why Not Raspbian?
-----------------

Mopidy with Spotify support is currently unavailable on the recommended
`Raspbian <http://www.raspbian.org>`_ Debian distribution that the Raspberry Pi
foundation has made available. This is due to Raspbian's hardware
floating-point support. The Raspberry Pi comes with a co-processor designed
specifically for floating-point computations (commonly called an FPU). Taking
advantage of the FPU can speed up many computations significantly over
software-emulated floating point routines. Most of Mopidy's dependencies are
open-source and have been (or can be) compiled to support the ``armhf``
architecture. However, there is one component of Mopidy's stack which is
closed-source and crucial to Mopidy's Spotify support: libspotify.

The ARM distributions of libspotify available on `Spotify's developer website
<http://developer.spotify.com>`_ are compiled for the ``armel`` architecture,
which has software floating-point support. ``armel`` and ``armhf`` software
cannot be mixed, and pyspotify links with libspotify as C extensions.  Thus,
Mopidy will not run with Spotify support on ``armhf`` distributions.

If the Spotify folks ever release builds of libspotify with ``armhf`` support,
Mopidy *should* work on Raspbian.


Support
=======

If you had trouble with the above or got Mopidy working a different way on
Raspberry Pi, please send us a pull request to update this page with your new
information. As usual, the folks at ``#mopidy`` on ``irc.freenode.net`` may be
able to help with any problems encountered.
