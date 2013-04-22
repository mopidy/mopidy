**************
Running Mopidy
**************

To start Mopidy, simply open a terminal and run::

    mopidy

When Mopidy says ``MPD server running at [127.0.0.1]:6600`` it's ready to
accept connections by any MPD client. Check out our non-exhaustive
:doc:`/clients/mpd` list to find recommended clients.

To stop Mopidy, press ``CTRL+C`` in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the TERM signal, e.g. by
using ``kill``::

    kill `ps ax | grep mopidy | grep -v grep | cut -d' ' -f1`

This can be useful e.g. if you create init script for managing Mopidy.


mopidy command
==============

.. program:: mopidy

.. cmdoption:: --version

    Show Mopidy's version number and exit.

.. cmdoption:: -h, --help

    Show help message and exit.

.. cmdoption:: -q, --quiet

    Show less output: warning level and higher.

.. cmdoption:: -v, --verbose

    Show more output: debug level and higher.

.. cmdoption:: --save-debug-log

    Save debug log to the file specified in the :confval:`logging/debug_file`
    config value, typically ``./mopidy.conf``.

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



mopidy-scan command
===================

.. program:: mopidy-scan

.. cmdoption:: --version

    Show Mopidy's version number and exit.

.. cmdoption:: -h, --help

    Show help message and exit.

.. cmdoption:: -q, --quiet

    Show less output: warning level and higher.

.. cmdoption:: -v, --verbose

    Show more output: debug level and higher.


.. _mopidy-convert-config:

mopidy-convert-config command
=============================

.. program:: mopidy-convert-config

This program does not take any options. It looks for the pre-0.14 settings file
at ``$XDG_CONFIG_DIR/mopidy/settings.py``, and if it exists it converts it and
ouputs a Mopidy 0.14 compatible ini-format configuration. If you don't already
have a config file at ``$XDG_CONFIG_DIR/mopidy/mopidy.conf``, you're asked if
you want to save the converted config to that file.

Example usage::

    $ cat ~/.config/mopidy/settings.py
    LOCAL_MUSIC_PATH = u'~/music'
    MPD_SERVER_HOSTNAME = u'::'
    SPOTIFY_PASSWORD = u'secret'
    SPOTIFY_USERNAME = u'alice'

    $ mopidy-convert-config
    Checking /home/alice/.config/mopidy/settings.py
    Converted config:

    [spotify]
    username = alice
    password = ********

    [mpd]
    hostname = ::

    [local]
    media_dir = ~/music

    Write new config to /home/alice/.config/mopidy/mopidy.conf? [yN] y
    Done.

    $ cat ~/.config/mopidy/mopidy.conf
    [spotify]
    username = alice
    password = secret

    [mpd]
    hostname = ::

    [local]
    media_dir = ~/music
