.. _raspberrypi-installation:

************
Raspberry Pi
************

Mopidy runs on all versions of `Raspberry Pi <https://www.raspberrypi.org/>`_.
However, note that the Raspberry Pi 2 and 3 are significantly more powerful than
the Raspberry Pi 1 and Raspberry Pi Zero; Mopidy will run noticably faster on
the later models.

.. image:: raspberrypi2.jpg
    :width: 640
    :height: 363


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

   - Change the password of the ``pi`` user.
   - Change the language, time zone, etc.

   Under "Advanced Options":

   - Set a hostname.
   - Enable SSH if not already enabled.
   - Force a specific audio output.
     By default, when using a HDMI display the
     audio will also be output over HDMI, otherwise the 3.5mm jack will be used.
   - Adjust the memory split.
     If you're not using a display (i.e. Raspbian
     Lite), you should set the minimum value here in order to make best use of
     the available RAM.

   Once done, select "Finish". Depending on what you changed you may be asked if
   you want to restart your Pi, select "Yes" and then log back in again
   afterwards.

   If you want to change any settings later, you can simply rerun ``sudo
   raspi-config``.


#. Install Mopidy and any Mopidy extensions you want, as described in
   :ref:`debian-install`.

.. note::

   If you used the Raspbian *Desktop* image you may also need to add the
   ``mopidy`` user to the ``video`` group. Run ``sudo adduser mopidy video``
   to do this.


Testing sound output
====================

You can test sound output independent of Mopidy by running::

    aplay /usr/share/sounds/alsa/Front_Center.wav

If you hear a voice saying "Front Center", then your sound is working.

If you want to change your audio output setting, simply rerun ``sudo
raspi-config``.
