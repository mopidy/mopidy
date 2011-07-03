.. _backend-controller-api:

**********************
Backend controller API
**********************


The backend controller API is the interface that is used by frontends like
:mod:`mopidy.frontends.mpd`. If you want to implement your own backend, see the
:ref:`backend-provider-api`.


The backend
===========

.. autoclass:: mopidy.backends.base.Backend
    :members:


Playback controller
===================

Manages playback, with actions like play, pause, stop, next, previous, and
seek.

.. autoclass:: mopidy.backends.base.PlaybackController
    :members:


Mixer controller
================

Manages volume. See :class:`mopidy.mixers.base.BaseMixer`.


Current playlist controller
===========================

Manages everything related to the currently loaded playlist.

.. autoclass:: mopidy.backends.base.CurrentPlaylistController
    :members:


Stored playlists controller
===========================

Manages stored playlist.

.. autoclass:: mopidy.backends.base.StoredPlaylistsController
    :members:


Library controller
==================

Manages the music library, e.g. searching for tracks to be added to a playlist.

.. autoclass:: mopidy.backends.base.LibraryController
    :members:
