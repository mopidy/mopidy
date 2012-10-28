.. _backend-api:

***********
Backend API
***********

.. module:: mopidy.backends.base
    :synopsis: The API implemented by backends

The backend API is the interface that must be implemented when you create a
backend. If you are working on a frontend and need to access the backend, see
the :ref:`core-api`.


Playback provider
=================

.. autoclass:: mopidy.backends.base.BasePlaybackProvider
    :members:


Stored playlists provider
=========================

.. autoclass:: mopidy.backends.base.BaseStoredPlaylistsProvider
    :members:


Library provider
================

.. autoclass:: mopidy.backends.base.BaseLibraryProvider
    :members:


.. _backend-implementations:

Backend implementations
=======================

* :mod:`mopidy.backends.dummy`
* :mod:`mopidy.backends.spotify`
* :mod:`mopidy.backends.local`
