# Install from system packages

Install Mopidy from your operating system's package manager to get automatic
updates alongside the rest of your system. If your OS or distribution is not
listed below, see [Manual install](manual.md).

//// tab | Debian/Ubuntu
If you run a Debian based Linux distribution, like Ubuntu or Raspberry Pi OS,
install from the [Mopidy APT archive](https://apt.mopidy.com/). The packages
here are built from the same source as the packages in Debian proper, just
updated more often than the Debian release cycle.

If you're setting up a Raspberry Pi from scratch, see the
[Raspberry Pi guide](../guides/raspberrypi.md) first.

Add the archive's GPG key:

```console
$ sudo mkdir -p /etc/apt/keyrings
$ sudo wget -q -O /etc/apt/keyrings/mopidy-archive-keyring.gpg \
  https://apt.mopidy.com/mopidy-archive-keyring.gpg
```

Add the APT repo to your package sources:

/// tab | Debian 13 (Trixie)
Also works on Ubuntu 25.10 and Raspberry Pi OS 2025-10-01 or newer.

```console
$ sudo wget -q -O /etc/apt/sources.list.d/mopidy.sources \
  https://apt.mopidy.com/trixie.sources
```

///

/// tab | Debian 12 (Bookworm)
Also works on Ubuntu 23.10 and Raspberry Pi OS 2023-10-10 or newer.

```console
$ sudo wget -q -O /etc/apt/sources.list.d/mopidy.sources \
  https://apt.mopidy.com/bookworm.sources
```

///

Install Mopidy and all dependencies:

```console
$ sudo apt update
$ sudo apt install mopidy
```

////

//// tab | Arch Linux
Install from the [Extra repository](https://www.archlinux.org/packages/extra/any/mopidy/):

```console
$ pacman -S mopidy
```

////

//// tab | Fedora
Install from the standard Fedora repositories:

```console
$ sudo dnf install mopidy
```

This will automatically install mopidy-mpd as a weak dependency as well.

Some extensions are packaged in RPMFusion. To
[install this repository](https://rpmfusion.org/Configuration), run:

```console
$ sudo dnf install \
  https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

////

//// tab | macOS
Install using [Homebrew](https://brew.sh/). First, enable the
[Mopidy Homebrew tap](https://github.com/mopidy/homebrew-mopidy):

```console
$ brew tap mopidy/mopidy
```

Then install Mopidy:

```console
$ brew install mopidy
```

This will take some time, as it also installs GStreamer and its media codecs.
////

Now, you're ready to [run Mopidy](../usage/index.md).

## Upgrade Mopidy

/// tab | Debian/Ubuntu

```console
$ sudo apt update
$ sudo apt upgrade
```

///

/// tab | Arch Linux

```console
$ pacman -Syu
```

///

/// tab | Fedora

```console
$ sudo dnf upgrade
```

///

/// tab | macOS

```console
$ brew upgrade
```

///

## Install extensions

/// tab | Debian/Ubuntu
To list extensions available from apt.mopidy.com:

```console
$ apt search mopidy
```

To install one, e.g. `mopidy-mpd`:

```console
$ sudo apt install mopidy-mpd
```

If the extension you want is not in APT, install it from PyPI using `pip`:

```console
$ sudo apt install python3-pip
$ sudo python3 -m pip install --break-system-packages ...
```

///

/// tab | Arch Linux
AUR has packages for many [Mopidy extensions](https://aur.archlinux.org/packages/?K=mopidy).
To install one, e.g. `mopidy-mpd`:

```console
$ yay -S mopidy-mpd
```

If the extension you want is not in AUR, install it from PyPI using `pip`:

```console
$ sudo python3 -m pip install --break-system-packages ...
```

///

/// tab | Fedora
As of February 2020, only mopidy-mpd (automatically installed) and
mopidy-spotify (RPMFusion-nonfree) are packaged.

To install `mopidy-spotify` from RPMFusion-nonfree:

```console
$ sudo dnf install mopidy-spotify
```

If the extension you want is not in the repositories, install it from PyPI
using `pip`:

```console
$ sudo python3 -m pip install ...
```

///

/// tab | macOS
The Homebrew tap has formulas for several Mopidy extensions. Extensions
installed from Homebrew come complete with all dependencies, both Python
and non-Python. To list available extensions:

```console
$ brew search mopidy
```

If the extension you want is not in Homebrew, install it from PyPI using
`pip`:

```console
$ python3 -m pip install ...
```

///

For a comprehensive index of available extensions, see the
[Mopidy extension registry](https://mopidy.com/ext/).
