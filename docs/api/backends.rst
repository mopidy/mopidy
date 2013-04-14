.. _backend-api:

***********
Backend API
***********

.. module:: mopidy.backends.base
    :synopsis: The API implemented by backends

The backend API is the interface that must be implemented when you create a
backend. If you are working on a frontend and need to access the backend, see
the :ref:`core-api`.


Backend class
=============

.. autoclass:: mopidy.backends.base.Backend
    :members:


Playback provider
=================

.. autoclass:: mopidy.backends.base.BasePlaybackProvider
    :members:


Playlists provider
==================

.. autoclass:: mopidy.backends.base.BasePlaylistsProvider
    :members:


Library provider
================

.. autoclass:: mopidy.backends.base.BaseLibraryProvider
    :members:


Backend listener
================

.. autoclass:: mopidy.backends.listener.BackendListener
    :members:


.. _backend-implementations:

Backend implementations
=======================

* :mod:`mopidy.backends.dummy`
* :mod:`mopidy.backends.local`
* :mod:`mopidy.backends.spotify`
* :mod:`mopidy.backends.stream`
