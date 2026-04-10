# Raspberry Pi

Mopidy runs on all versions of [Raspberry Pi](https://www.raspberrypi.org/).
However, note that the later models are significantly more powerful than
the Raspberry Pi 1 and Raspberry Pi Zero; Mopidy will run noticeably faster on
the later models.

/// warning
This page is written for Raspbian and needs to be updated for
Raspberry Pi OS released 2025-12-04.
///

## Download the image

Download the latest Raspbian Desktop or Lite disk image from
<https://www.raspberrypi.org/downloads/raspbian/>.

Unless you need a full graphical desktop the Lite image is preferable since
it's much smaller.

## Flash to SD card

Flash the image you downloaded to your SD card. See the
[Raspberry Pi installation docs](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)
for instructions.

You'll need to enable SSH if you are not connecting a monitor and a keyboard.
As of the November 2016 release, Raspbian has the SSH server disabled by
default. SSH can be enabled by placing a file named `ssh`, without any
extension, onto the boot partition of the SD card. See the
[Raspberry Pi SSH documentation](https://www.raspberrypi.org/documentation/remote-access/ssh/README.md)
for more details.

## Connect via SSH

If you boot with only a network cable connected, you'll have to find the IP
address of the Pi yourself, e.g. by looking in the client list on your
router/DHCP server. When you have found the Pi's IP address, SSH to it and
login with the user `pi` and password `raspberry`. Once logged in, run
`sudo raspi-config` to start the config tool as the `root` user.

## Initial configuration

Use the `raspi-config` tool to set up the basics of your Pi. You might want
to do one or more of the following:

- In the top menu, change the password of the `pi` user.

- Under "Network Options":

    - N1: Set a hostname.
    - N2: Set up WiFi credentials, if you're going to use WiFi.

- Under "Localisation Options":

    - I1: Change locale from `en_GB.UTF-8` to e.g. `en_US.UTF-8`, that is,
      unless you're British.
    - I2: Change the time zone.
    - I4: Change the WiFi country, so you only use channels allowed in your area.

- Under "Interfacing Options":

    - P2: Enable SSH.

- Under "Advanced Options":

    - A3: Adjust the memory split. If you're not going to connect a display
      to your Pi, set the minimum value here to make best use of available RAM.
    - A4: Force a specific audio output. By default, when using an HDMI display
      the audio will also be output over HDMI, otherwise the 3.5mm jack is used.

Once done, select "Finish". Depending on what you changed you may be asked if
you want to restart your Pi, select "Yes" and then log back in again afterwards.

If you want to change any settings later, you can simply rerun `sudo raspi-config`.

## Configure audio

Ensure the system audio settings match the user audio settings:

```console
$ sudo ln -s ~/.asoundrc /etc/asound.conf
```

## Install Mopidy

Install Mopidy and any extensions you want, as described in
[the installation guide](../installation/index.md).

/// note
If you used the Raspbian *Desktop* image you will need to add the
`mopidy` user to the `video` group:

```console
$ sudo adduser mopidy video
```

Also, if you are *not* using HDMI audio you must set Mopidy's
[`audio/output`](../usage/config.md#audiooutput) config value to `alsasink`. To do this, add the following
snippet to your [config](../usage/config.md) file:

```ini title="mopidy.conf"
[audio]
output = alsasink
```

///

## Testing sound output

You can test sound output independent of Mopidy by running:

```console
$ aplay /usr/share/sounds/alsa/Front_Center.wav
```

If you hear a voice saying "Front Center", then your sound is working.

If you want to change your audio output setting, simply rerun `sudo raspi-config`.
