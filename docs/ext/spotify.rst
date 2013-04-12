.. _ext-spotify:

**************
Mopidy-Spotify
**************

An extension for playing music from Spotify.

`Spotify <http://www.spotify.com/>`_ is a music streaming service. The backend
uses the official `libspotify
<http://developer.spotify.com/en/libspotify/overview/>`_ library and the
`pyspotify <http://github.com/mopidy/pyspotify/>`_ Python bindings for
libspotify. This backend handles URIs starting with ``spotify:``.

.. note::

    This product uses SPOTIFY(R) CORE but is not endorsed, certified or
    otherwise approved in any way by Spotify. Spotify is the registered
    trade mark of the Spotify Group.


Known issues
============

https://github.com/mopidy/mopidy/issues?labels=Spotify+backend


Dependencies
============

.. literalinclude:: ../../requirements/spotify.txt


Default configuration
=====================

.. literalinclude:: ../../mopidy/backends/spotify/ext.conf
    :language: ini


Configuration values
====================

.. confval:: spotify/enabled

    If the Spotify extension should be enabled or not.

.. confval:: spotify/username

    Your Spotify Premium username.

.. confval:: spotify/password

    Your Spotify Premium password.

.. confval:: spotify/bitrate

    The preferred audio bitrate. Valid values are 96, 160, 320.

.. confval:: spotify/timeout

    Max number of seconds to wait for Spotify operations to complete.

.. confval:: spotify/cache_dir

    Path to the Spotify data cache. Cannot be shared with other Spotify apps.


Usage
=====

If you are using the Spotify backend, which is the default, enter your Spotify
Premium account's username and password into ``~/.config/mopidy/mopidy.conf``,
like this:

.. code-block:: ini

    [spotify]
    username = myusername
    password = mysecret

This will only work if you have the Spotify Premium subscription. Spotify
Unlimited will not work.
