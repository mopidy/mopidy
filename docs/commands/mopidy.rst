.. _mopidy-cmd:

**************
mopidy command
**************

Synopsis
========

mopidy
    [-h] [--version] [-q] [-v] [--save-debug-log] [--show-config]
    [--show-deps] [--config CONFIG_FILES] [-o CONFIG_OVERRIDES]


Description
===========

Mopidy is a music server which can play music both from multiple sources, like
your local hard drive, radio streams, and from Spotify and SoundCloud. Searches
combines results from all music sources, and you can mix tracks from all
sources in your play queue. Your playlists from Spotify or SoundCloud are also
available for use.

The ``mopidy`` command is used to start the server.


Options
=======

.. program:: mopidy

.. cmdoption:: -h, --help

    Show help message and exit.

.. cmdoption:: --version

    Show Mopidy's version number and exit.

.. cmdoption:: -q, --quiet

    Show less output: warning level and higher.

.. cmdoption:: -v, --verbose

    Show more output: debug level and higher.

.. cmdoption:: --save-debug-log

    Save debug log to the file specified in the :confval:`logging/debug_file`
    config value, typically ``./mopidy.log``.

.. cmdoption:: --show-config

    Show the current effective config. All configuration sources are merged
    together to show the effective document. Secret values like passwords are
    masked out. Config for disabled extensions are not included.

.. cmdoption:: --show-deps

    Show dependencies, their versions and installation location.

.. cmdoption:: --config <file>

    Specify config file to use. To use multiple config files, separate them
    with colon. The later files override the earlier ones if there's a
    conflict.

.. cmdoption:: -o <option>, --option <option>

    Specify additional config values in the ``section/key=value`` format. Can
    be provided multiple times.


Files
=====

/etc/mopidy/mopidy.conf
    System wide Mopidy configuration file.

~/.config/mopidy/mopidy.conf
    Your personal Mopidy configuration file. Overrides any configs from the
    system wide configuration file.


Examples
========

To start the music server, run::

    mopidy

To start the server with an additional config file than can override configs
set in the default config files, run::

    mopidy --config ./my-config.conf

To start the server and change a config value directly on the command line,
run::

    mopidy --option mpd/enabled=false

The :option:`--option` flag may be repeated multiple times to change multiple
configs::

    mopidy -o mpd/enabled=false -o spotify/bitrate=320

The :option:`--show-config` output shows the effect of the :option:`--option`
flags::

    mopidy -o mpd/enabled=false -o spotify/bitrate=320 --show-config


See also
========

:ref:`mopidy-scan(1) <mopidy-scan-cmd>`, :ref:`mopidy-convert-config(1)
<mopidy-convert-config>`

Reporting bugs
==============

Report bugs to Mopidy's issue tracker at
<https://github.com/mopidy/mopidy/issues>
