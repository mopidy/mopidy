# Manual install

If you are on Linux or macOS, but can't install from a package manager,
you can install Mopidy from PyPI using `pip`.

## Python

You need Python 3.13 or newer. Check if you have Python and what version by
running:

```console
$ python3 --version
```

## pip and build tools

You need `pip`, the Python package installer. You'll also need a C compiler
and the Python development headers to install some Mopidy extensions.

/// tab | Debian/Ubuntu

```console
$ sudo apt install build-essential python3-dev python3-pip
```

///

/// tab | Arch Linux

```console
$ sudo pacman -S base-devel python-pip
```

///

/// tab | Fedora

```console
$ sudo dnf install -y gcc python3-devel python3-pip
```

///

/// tab | Gentoo

```console
$ emerge -av dev-python/pip
```

///

/// tab | macOS
pip is included with Python when installed via Homebrew or python.org.
///

## GStreamer

You'll need GStreamer >= 1.26.2. GStreamer is packaged for most popular Linux
distributions. Search for GStreamer in your package manager and make sure to
install the "good" and "ugly" plugin sets, as well as the Python bindings.
To be able to build the Python bindings from source, also install the
development headers for `libcairo2` and `libgirepository-2.0`.

/// tab | Debian/Ubuntu

```console
$ sudo apt install \
    gir1.2-gst-plugins-base-1.0 \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    libcairo2-dev \
    libgirepository-2.0-dev \
    python3-gst-1.0
```

///

/// tab | Arch Linux

```console
$ sudo pacman -S \
    cairo \
    gobject-introspection \
    gst-python \
    gst-plugins-good \
    gst-plugins-ugly
```

///

/// tab | Fedora

```console
$ sudo dnf install -y \
    cairo-devel \
    gobject-introspection-devel \
    python3-gstreamer1 \
    gstreamer1-plugins-good \
    gstreamer1-plugins-ugly-free
```

///

/// tab | Gentoo

```console
$ emerge -av \
    dev-libs/gobject-introspection \
    dev-python/gst-python \
    media-plugins/gst-plugins-meta \
    x11-libs/cairo
```

`gst-plugins-meta` is the one that actually pulls in the plugins you want,
so pay attention to the USE flags, e.g. `alsa`, `mp3`, etc.
///

/// tab | macOS

```console
$ brew install \
    cairo \
    gobject-introspection \
    gst-python \
    gst-plugins-base \
    gst-plugins-good \
    gst-plugins-ugly
```

///

## Mopidy

You are now ready to install the latest release of Mopidy.

If you're installing Mopidy inside a Python virtual environment, activate the
virtualenv and run:

```console
$ python3 -m pip install --upgrade mopidy
```

If you want to install Mopidy globally on your system, you can run:

```console
$ sudo python3 -m pip install --upgrade --break-system-packages mopidy
```

This will use `pip` to install the latest release of
[Mopidy from PyPI](https://pypi.org/project/Mopidy).
To upgrade Mopidy in the future, just rerun the same command.

Now, you're ready to [run Mopidy](../usage/index.md).

## Extensions

If you want to use any Mopidy extensions, like Spotify support or MPD client
access, you need to install them separately.

You can install any Mopidy extension directly from PyPI with `pip`.
Browse the [extension registry](https://mopidy.com/ext/) to find available
extensions. To install one, e.g. `mopidy-mpd`, inside a virtualenv, run:

```console
$ python3 -m pip install mopidy-mpd
```

To install the same package globally on your system, run:

```console
$ sudo python3 -m pip install --break-system-packages mopidy-mpd
```

Note that extensions installed with `pip` will only install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.
