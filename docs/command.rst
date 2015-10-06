.. _mopidy-cmd:

**************
mopidy command
**************

Synopsis
========

mopidy
    [-h] [--version] [-q] [-v] [--save-debug-log] [--config CONFIG_FILES]
    [-o CONFIG_OVERRIDES] [COMMAND] ...


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

.. cmdoption:: --help, -h

    Show help message and exit.

.. cmdoption:: --version

    Show Mopidy's version number and exit.

.. cmdoption:: --quiet, -q

    Show less output: warning level and higher.

.. cmdoption:: --verbose, -v

    Show more output. Repeat up to four times for even more.

.. cmdoption:: --save-debug-log

    Save debug log to the file specified in the :confval:`logging/debug_file`
    config value, typically ``./mopidy.log``.

.. cmdoption:: --config <file|directory>

    Specify config files and directories to use. To use multiple config files
    or directories, separate them with a colon. The later files override the
    earlier ones if there's a conflict. When specifying a directory, all files
    ending in .conf in the directory are used.

.. cmdoption:: --option <option>, -o <option>

    Specify additional config values in the ``section/key=value`` format. Can
    be provided multiple times.


Built in commands
=================

.. cmdoption:: config

    Show the current effective config. All configuration sources are merged
    together to show the effective document. Secret values like passwords are
    masked out. Config for disabled extensions are not included.

.. cmdoption:: deps

    Show dependencies, their versions and installation location.


Extension commands
==================

Additionally, extensions can provide extra commands. Run `mopidy --help`
for a list of what is available on your system and command-specific help.
Commands for disabled extensions will be listed, but can not be run.

.. describe:: local clear

    Clear local media files from the local library.

.. describe:: local scan

    Scan local media files present in your library.


Files
=====

:file:`/etc/mopidy/mopidy.conf`
    System wide Mopidy configuration file.

:file:`~/.config/mopidy/mopidy.conf`
    Your personal Mopidy configuration file. Overrides any configs from the
    system wide configuration file.


Examples
========

To start the music server, run::

    mopidy

To start the server with an additional config file, that can override configs
set in the default config files, run::

    mopidy --config ./my-config.conf

To start the server and change a config value directly on the command line,
run::

    mopidy --option mpd/enabled=false

The :option:`--option` flag may be repeated multiple times to change multiple
configs::

    mopidy -o mpd/enabled=false -o spotify/bitrate=320

The ``mopidy config`` output shows the effect of the :option:`--option` flags::

    mopidy -o mpd/enabled=false -o spotify/bitrate=320 config


Reporting bugs
==============

Report bugs to Mopidy's issue tracker at
<https://github.com/mopidy/mopidy/issues>
