.. _backend-controller-api:

**********************
Backend controller API
**********************


The backend controller API is the interface that is used by frontends like
:mod:`mopidy.frontends.mpd`. If you want to implement your own backend, see the
:ref:`backend-provider-api`.


The backend
===========

.. autoclass:: mopidy.backends.base.BaseBackend
    :members:
    :undoc-members:


Playback controller
===================

Manages playback, with actions like play, pause, stop, next, previous, and
seek.

.. autoclass:: mopidy.backends.base.BasePlaybackController
    :members:
    :undoc-members:


Mixer controller
================

Manages volume. See :class:`mopidy.mixers.BaseMixer`.


Current playlist controller
===========================

Manages everything related to the currently loaded playlist.

.. autoclass:: mopidy.backends.base.BaseCurrentPlaylistController
    :members:
    :undoc-members:


Stored playlists controller
===========================

Manages stored playlist.

.. autoclass:: mopidy.backends.base.BaseStoredPlaylistsController
    :members:
    :undoc-members:


Library controller
==================

Manages the music library, e.g. searching for tracks to be added to a playlist.

.. autoclass:: mopidy.backends.base.BaseLibraryController
    :members:
    :undoc-members:
