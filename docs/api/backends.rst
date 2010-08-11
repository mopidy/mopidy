**********************
:mod:`mopidy.backends`
**********************

.. automodule:: mopidy.backends
    :synopsis: Backend API


The backend and its controllers
===============================

.. graph:: backend_relations

    backend -- current_playlist
    backend -- library
    backend -- playback
    backend -- stored_playlists


Backend API
===========

.. note::

    Currently this only documents the API that is available for use by
    frontends like :mod:`mopidy.frontends.mpd`, and not what is required to
    implement your own backend. :class:`mopidy.backends.base.BaseBackend` and
    its controllers implements many of these methods in a matter that should be
    independent of most concrete backend implementations, so you should
    generally just implement or override a few of these methods yourself to
    create a new backend with a complete feature set.

.. autoclass:: mopidy.backends.base.BaseBackend
    :members:
    :undoc-members:


Playback controller
-------------------

Manages playback, with actions like play, pause, stop, next, previous, and
seek.

.. autoclass:: mopidy.backends.base.BasePlaybackController
    :members:
    :undoc-members:


Mixer controller
----------------

Manages volume. See :class:`mopidy.mixers.BaseMixer`.


Current playlist controller
---------------------------

Manages everything related to the currently loaded playlist.

.. autoclass:: mopidy.backends.base.BaseCurrentPlaylistController
    :members:
    :undoc-members:


Stored playlists controller
---------------------------

Manages stored playlist.

.. autoclass:: mopidy.backends.base.BaseStoredPlaylistsController
    :members:
    :undoc-members:


Library controller
------------------

Manages the music library, e.g. searching for tracks to be added to a playlist.

.. autoclass:: mopidy.backends.base.BaseLibraryController
    :members:
    :undoc-members:


:mod:`mopidy.backends.despotify` -- Despotify backend
=====================================================

.. automodule:: mopidy.backends.despotify
    :synopsis: Spotify backend using the Despotify library
    :members:


:mod:`mopidy.backends.dummy` -- Dummy backend for testing
=========================================================

.. automodule:: mopidy.backends.dummy
    :synopsis: Dummy backend used for testing
    :members:


:mod:`mopidy.backends.libspotify` -- Libspotify backend
=======================================================

.. automodule:: mopidy.backends.libspotify
    :synopsis: Spotify backend using the libspotify library
    :members:


:mod:`mopidy.backends.local` -- Local backend
=====================================================

.. automodule:: mopidy.backends.local
    :synopsis: Backend for playing music files on local storage
    :members:
