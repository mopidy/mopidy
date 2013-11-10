.. _mopidy-cmd:

**************
mopidy command
**************

Synopsis
========

mopidy
    [-h] [--version] [-q] [-v] [--save-debug-log] [--config CONFIG_FILES]
    [-o CONFIG_OVERRIDES] COMMAND ...


Description
===========

Mopidy is a music server which can play music both from multiple sources, like
your local hard drive, radio streams, and from Spotify and SoundCloud. Searches
combines results from all music sources, and you can mix tracks from all
sources in your play queue. Your playlists from Spotify or SoundCloud are also
available for use.

The ``mopidy run`` command is used to start the server.


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

.. cmdoption:: --config <file>

    Specify config file to use. To use multiple config files, separate them
    with a colon. The later files override the earlier ones if there's a
    conflict.

.. cmdoption:: -o <option>, --option <option>

    Specify additional config values in the ``section/key=value`` format. Can
    be provided multiple times.


Built in sub-commands
=====================

.. cmdoption:: run

    Run the mopidy server.

.. cmdoption:: config

    Show the current effective config. All configuration sources are merged
    together to show the effective document. Secret values like passwords are
    masked out. Config for disabled extensions are not included.

.. cmdoption:: deps

    Show dependencies, their versions and installation location.


Extension sub-commands
======================

Additionally, extensions can provide extra sub-commands. See ``mopidy --help``
for a list of what is available on your system and ``mopidy COMMAND --help``
for command-specific help. Sub-commands for disabled extensions will be listed,
but can not be run.

.. cmdoption:: local

    Scan local media files present in your library.


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

    mopidy run

To start the server with an additional config file than can override configs
set in the default config files, run::

    mopidy --config ./my-config.conf run

To start the server and change a config value directly on the command line,
run::

    mopidy --option mpd/enabled=false run

The :option:`--option` flag may be repeated multiple times to change multiple
configs::

    mopidy -o mpd/enabled=false -o spotify/bitrate=320 run

``mopidy config`` output shows the effect of the :option:`--option` flags::

    mopidy -o mpd/enabled=false -o spotify/bitrate=320 config


See also
========

:ref:`mopidy-convert-config(1) <mopidy-convert-config>`

Reporting bugs
==============

Report bugs to Mopidy's issue tracker at
<https://github.com/mopidy/mopidy/issues>
