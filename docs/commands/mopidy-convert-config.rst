.. _mopidy-convert-config:

*****************************
mopidy-convert-config command
*****************************

Synopsis
========

mopidy-convert-config


Description
===========

Mopidy is a music server which can play music both from multiple sources, like
your local hard drive, radio streams, and from Spotify and SoundCloud. Searches
combines results from all music sources, and you can mix tracks from all
sources in your play queue. Your playlists from Spotify or SoundCloud are also
available for use.

The ``mopidy-convert-config`` command is used to convert :file:`settings.py`
configuration files used by ``mopidy`` < 0.14 to the :file:`mopidy.conf` config
file used by ``mopidy`` >= 0.14.


Options
=======

.. program:: mopidy-convert-config

This program does not take any options. It looks for the pre-0.14 settings file
at :file:`{$XDG_CONFIG_DIR}/mopidy/settings.py`, and if it exists it converts
it and ouputs a Mopidy 0.14 compatible ini-format configuration. If you don't
already have a config file at :file:`{$XDG_CONFIG_DIR}/mopidy/mopidy.conf``,
you're asked if you want to save the converted config to that file.


Example
=======

Given the following contents in :file:`~/.config/mopidy/settings.py`:

::

    LOCAL_MUSIC_PATH = u'~/music'
    MPD_SERVER_HOSTNAME = u'::'
    SPOTIFY_PASSWORD = u'secret'
    SPOTIFY_USERNAME = u'alice'

Running ``mopidy-convert-config`` will convert the config and create a new
:file:`mopidy.conf` config file:

.. code-block:: none

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

Contents of :file:`~/.config/mopidy/mopidy.conf` after the conversion:

.. code-block:: ini

    [spotify]
    username = alice
    password = secret

    [mpd]
    hostname = ::

    [local]
    media_dir = ~/music


See also
========

:ref:`mopidy(1) <mopidy-cmd>`


Reporting bugs
==============

Report bugs to Mopidy's issue tracker at
<https://github.com/mopidy/mopidy/issues>
