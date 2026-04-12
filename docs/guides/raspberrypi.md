# Raspberry Pi

This guide will show you the golden path to get Mopidy up and running on a
Raspberry Pi, but there are many possible variations depending on what model you
have, what audio output accessories you have, and what Linux distribution you
run on your Raspberry Pi. We cannot cover all of those variations here, but we
try to cover the most common setup.

Mopidy runs on most versions of [Raspberry Pi](https://www.raspberrypi.org/),
but we recommend using a Raspberry Pi 3 or later for the best experience.

If anything here is unclear, please refer to Raspberry Pi's excellent [getting
started documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html).

This guide was last tested using the Raspberry Pi OS (64-bit) Lite image, dated
2025-12-04, on a Raspberry Pi 3 Model B with 1GB of memory and a 16GB SD card,
with audio output through the 3.5mm audio jack. The instructions should be
similar for other models and configurations, but your mileage may vary.

## Prepare the SD card

Install and run the [Raspberry Pi Imager](https://www.raspberrypi.com/software/),
and follow these instructions to flash an OS image to your SD card:

- **Device:** Select your type of device, typically Raspberry Pi 3, 4, or 5.

- **OS:** When selecting the OS, you probably want to navigate into the "Raspberry
  Pi OS (other)" category to find the "Raspberry Pi OS (64-bit) Lite" variant,
  to save on both memory usage and disk space.

- **Storage:** Select the SD card you want to write the OS onto.

- **Customisation:** In the customization steps, you can set the Pi's hostname.
  We recommend that you enable SSH, and set up WiFi credentials so that the
  device can connect to the network on first boot, removing the need to connect
  a monitor and keyboard to the device for the initial setup.

- **Writing:** Confirm the previous choices and wait for the OS image to be written
  to the SD card. This may take a few minutes.

/// note | WiFi and WPA support
If using a Raspberry Pi older than 3B+, e.g. 3B, remember that it doesn't
support 5GHz WiFi or WPA3. Depending on Raspberry Pi model, you may need to set
up a 2.4GHz WiFi network with WPA2 security for the Pi to be able to connect to
the network.
///

## Connect via SSH

Insert the SD card into the Raspberry Pi, connect a network cable if you're not
using WiFi, and power it on. The Pi will boot and connect to the network, and
you should be able to connect to it via SSH.

To find the IP address of the Pi, you have two options:

- Look in the client list on your Internet router's DHCP server. Look for a
  device with the hostname you set up in the previous step, or a device with the
  manufacturer "Raspberry Pi Foundation".

- Connect the Pi to a monitor. It'll print its current IPv4 and IPv6 address to
  the console at the end of the boot sequence, just before the login prompt or
  shell appears. If you have a keyboard connected, you can run the command
  `hostname -I` to print the IP address at any time.

When you have found the Pi's IP address, SSH to it, and login using the
credentials you set up in the previous step:

```console
$ ssh <username>@<ip-address>
```

## Update the system

Once connected through SSH, it's a good idea to update the system as the image
may be a few months old and missing important security updates and bug fixes.
You can do this by running the following commands:

```console
$ sudo apt update
$ sudo apt upgrade -y
```

## Initial configuration

Next, use the `raspi-config` tool to set up the basics of your Pi:

```console
$ sudo raspi-config
```

The tool lets you change many of the choices you made when creating the SD card
with Imager. You might also want to have a look at the following settings:

- **System Options > S2 Audio:**

    Select if you want audio output via the HDMI port or the 3.5mm audio jack.

    /// tip | Contribute
    Using a USB audio card or a HAT for audio output? Please let us know how the
    setup differs and help us document this.
    ///

- **System Options > S5 Boot:**

    If you didn't use the Lite image and have a full desktop environment on your
    Pi, you can select "B1 Console Text console" to save some memory and CPU
    resources by not starting the desktop environment on boot.

- **System Options > S6 Auto Login:**

    For a bit better security, you can disable auto login and require a password
    to log in to the Pi when physically connecting with a monitor and a
    keyboard.

- **Localisation Options > L1 Locale:**

    If you want to save some space and time during upgrades, you can unselect
    the `en_GB.UTF-8` locale.

    On the next screen, select `C.UTF-8` as the default locale instead of
    `None`. Explicitly selecting the Pi's locale fixes warnings about
    mismatching locales when you SSH in from a machine with a different locale.

Once done, select "Finish". Depending on what you changed you may be asked if
you want to restart your Pi, select "Yes" and then log back in again afterwards.

To manually reboot the device, you can run:

```console
$ sudo reboot
```

If you want to change any settings later, you can simply rerun `sudo raspi-config`.

## Testing sound output

You can test sound output independent of Mopidy by running:

```console
$ aplay /usr/share/sounds/alsa/Front_Center.wav
```

If you hear a voice saying "Front Center", then your sound is working.

If you want to change your audio output setting, simply rerun `sudo raspi-config`.

## Install Mopidy with Spotify support

Now we're done with everything specific to the Raspberry Pi, and we can follow
the same instructions as for any other Debian-based system to install Mopidy and
the Spotify extension.

Next, follow the instructions in the [Spotify on Debian-based
systems](debian.md) guide.
