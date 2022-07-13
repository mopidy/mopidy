.. _raspberrypi-installation:

************
Raspberry Pi
************

Mopidy runs on all versions of `Raspberry Pi <https://www.raspberrypi.org/>`_.
However, note that the later models are significantly more powerful than
the Raspberry Pi 1 and Raspberry Pi Zero; Mopidy will run noticably faster on
the later models.


How to for Raspbian
===================

#. Download the latest Raspbian Desktop or Lite disk image from
   https://www.raspberrypi.org/downloads/raspbian/.

   Unless you need a full graphical desktop the Lite image is preferable since
   it's much smaller.

#. Flash the Raspbian image you downloaded to your SD card.

   See the `Raspberry Pi installation docs
   <https://www.raspberrypi.org/documentation/installation/installing-images/README.md>`_
   for instructions.

   You'll need to enable SSH if you are not connecting a monitor and a keyboard.
   As of the November 2016 release, Raspbian has the SSH server disabled by
   default. SSH can be enabled by placing a file named 'ssh', without any
   extension, onto the boot partition of the SD card. See `here
   <https://www.raspberrypi.org/documentation/remote-access/ssh/README.md>`_ for
   more details.

#. If you boot with only a network cable connected, you'll have to find the IP
   address of the Pi yourself, e.g. by looking in the client list on your
   router/DHCP server. When you have found the Pi's IP address, you can SSH to
   the IP address and login with the user ``pi`` and password ``raspberry``.
   Once logged in, run ``sudo raspi-config`` to start the config tool as the
   ``root`` user.

#. Use the ``raspi-config`` tool to setup the basics of your Pi. You might want
   to do one or more of the following:

   - In the top menu, change the password of the ``pi`` user.

   - Under "Network Options":

     - N1: Set a hostname.
     - N2: Set up WiFi credentials, if you're going to use WiFi.

   - Under "Localisation Options":

     - I1: Change locale from ``en_GB.UTF-8`` to e.g. ``en_US.UTF-8``, that is,
       unless you're British.
     - I2: Change the time zone.
     - I4: Change the WiFi country, so you only use channels allowed to use in your area.

   - Under "Interfacing Options":

     - P2: Enable SSH.

   - Under "Advanced Options":

     - A3: Adjust the memory split.
       If you're not going to connect a display to your Pi, you should set the
       minimum value here in order to make best use of the available RAM.
     - A4: Force a specific audio output.
       By default, when using a HDMI display the
       audio will also be output over HDMI, otherwise the 3.5mm jack will be used.

   Once done, select "Finish". Depending on what you changed you may be asked if
   you want to restart your Pi, select "Yes" and then log back in again
   afterwards.

   If you want to change any settings later, you can simply rerun ``sudo
   raspi-config``.

#. Ensure the system audio settings match the user audio settings::

       sudo ln -s ~/.asoundrc /etc/asound.conf

#. Install Mopidy and any Mopidy extensions you want, as described in
   :ref:`debian-install`.

.. note::

   If you used the Raspbian *Desktop* image you will need to add the
   ``mopidy`` user to the ``video`` group::

       sudo adduser mopidy video

   Also, if you are *not* using HDMI audio you must set Mopidy's
   ``audio/output`` config value to ``alsasink``. To do this, add the following
   snippet to your :doc:`config </config>` file::

       [audio]
       output = alsasink


Testing sound output
====================

You can test sound output independent of Mopidy by running::

    aplay /usr/share/sounds/alsa/Front_Center.wav

If you hear a voice saying "Front Center", then your sound is working.

If you want to change your audio output setting, simply rerun ``sudo
raspi-config``.
