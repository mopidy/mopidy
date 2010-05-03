**********************
:mod:`mopidy.backends`
**********************

The backend and its controllers
===============================

.. graph:: backend_relations

    backend -- current_playlist
    backend -- library
    backend -- playback
    backend -- stored_playlists


Backend API
===========

.. automodule:: mopidy.backends
    :synopsis: Backend interface.

.. note::

    Currently this only documents the API that is available for use by
    frontends like :class:`mopidy.mpd.handler`, and not what is required to
    implement your own backend. :class:`mopidy.backends.BaseBackend` and its
    controllers implements many of these methods in a matter that should be
    independent of most concrete backend implementations, so you should
    generally just implement or override a few of these methods yourself to
    create a new backend with a complete feature set.

.. autoclass:: mopidy.backends.BaseBackend
    :members:
    :undoc-members:


Playback controller
-------------------

Manages playback, with actions like play, pause, stop, next, previous, and
seek.

.. autoclass:: mopidy.backends.BasePlaybackController
    :members:
    :undoc-members:


Mixer controller
----------------

Manages volume. See :class:`mopidy.mixers.BaseMixer`.


Current playlist controller
---------------------------

Manages everything related to the currently loaded playlist.

.. autoclass:: mopidy.backends.BaseCurrentPlaylistController
    :members:
    :undoc-members:


Stored playlists controller
---------------------------

Manages stored playlist.

.. autoclass:: mopidy.backends.BaseStoredPlaylistsController
    :members:
    :undoc-members:


Library controller
------------------

Manages the music library, e.g. searching for tracks to be added to a playlist.

.. autoclass:: mopidy.backends.BaseLibraryController
    :members:
    :undoc-members:


Spotify backends
================

:mod:`mopidy.backends.despotify` -- Despotify backend
-----------------------------------------------------

.. automodule:: mopidy.backends.despotify
    :synopsis: Spotify backend using the despotify library.
    :members:


:mod:`mopidy.backends.libspotify` -- Libspotify backend
-------------------------------------------------------

.. automodule:: mopidy.backends.libspotify
    :synopsis: Spotify backend using the libspotify library.
    :members:


Other backends
==============

:mod:`mopidy.backends.dummy` -- Dummy backend
---------------------------------------------

.. automodule:: mopidy.backends.dummy
    :synopsis: Dummy backend used for testing.
    :members:


:mod:`mopidy.backends.gstreamer` -- GStreamer backend
-----------------------------------------------------

.. automodule:: mopidy.backends.gstreamer
    :synopsis: Backend for playing music from a local music archive using the
        GStreamer library.
    :members:
