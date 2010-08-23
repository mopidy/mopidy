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

You may also want to change some of the ``LOCAL_*`` settings. See
:mod:`mopidy.settings`, for a full list of available settings.


Connecting from other machines on the network
=============================================

As a secure default, Mopidy only accepts connections from ``localhost``. If you
want to open it for connections from other machines on your network, see
the documentation for :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`.
