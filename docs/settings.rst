********
Settings
********

Mopidy reads settings from the file ``~/.mopidy/settings.py``, where ``~``
means your *home directory*. If your username is ``alice`` and you are running
Linux, the settings file should probably be at
``/home/alice/.mopidy/settings.py``.

You can either create this file yourself, or run the ``mopidy`` command, and it
will create an empty settings file for you.


Music from Spotify
==================

If you are using the Spotify backend, which is the default, enter your Spotify
Premium account's username and password into the file, like this::

    SPOTIFY_USERNAME = u'myusername'
    SPOTIFY_PASSWORD = u'mysecret'


Music from local storage
========================

If you want use Mopidy to play music you have locally at your machine instead
of using Spotify, you need to change the backend from the default to
:mod:`mopidy.backends.local` by adding the following line to your settings
file::

    BACKENDS = (u'mopidy.backends.local.LocalBackend',)

Previously this backend relied purely on ``tag_cache`` files from MPD, to
remedy this the command ``mopidy-scan`` has been added. This program will scan
your current ``LOCAL_MUSIC_FOLDER`` and build a MPD compatible ``tag_cache``.
Currently the command outputs the ``tag_cache`` to ``stdout``, this means that
you will need to run ``mopidy-scan > path/to/your/tag_cache`` to actually start
using your new cache.

You may also want to change some of the ``LOCAL_*`` settings. See
:mod:`mopidy.settings`, for a full list of available settings.


Connecting from other machines on the network
=============================================

As a secure default, Mopidy only accepts connections from ``localhost``. If you
want to open it for connections from other machines on your network, see
the documentation for :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`.


Scrobbling tracks to Last.fm
============================

If you want to submit the tracks you are playing to your `Last.fm
<http://www.last.fm/>`_ profile, make sure you've installed the dependencies
found at :mod:`mopidy.frontends.lastfm` and add the following to your settings
file::

    LASTFM_USERNAME = u'myusername'
    LASTFM_PASSWORD = u'mysecret'
