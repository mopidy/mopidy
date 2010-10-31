**********************
:mod:`mopidy.backends`
**********************

.. automodule:: mopidy.backends
    :synopsis: Backend API


The backend, controller, and provider concepts
==============================================

Backend:
    The backend is mostly for convenience. It is a container that holds
    references to all the controllers.
Controllers:
    Each controller has responsibility for a given part of the backend
    functionality. Most, but not all, controllers delegates some work to one or
    more providers. The controllers are responsible for choosing the right
    provider for any given task based upon i.e. the track's URI.
Providers:
    Anything specific to i.e. Spotify integration or local storage is contained
    in the providers. To integrate with new music sources, you just add new
    providers.

.. digraph:: backend_relations

    Backend -> "Current\nplaylist\ncontroller"
    Backend -> "Library\ncontroller"
    "Library\ncontroller" -> "Library\nproviders"
    Backend -> "Playback\ncontroller"
    "Playback\ncontroller" -> "Playback\nproviders"
    Backend -> "Stored\nplaylists\ncontroller"
    "Stored\nplaylists\ncontroller" -> "Stored\nplaylist\nproviders"
    Backend -> Mixer

.. _backend-api:

Backend API
===========

.. note::

    The backend API is the interface that is used by frontends like
    :mod:`mopidy.frontends.mpd`. If you want to implement your own backend, see
    the :ref:`provider-api`.

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


.. _provider-api:

Provider API
============

.. note::

    The provider API is the interface that must be implemented when you create
    a backend. If you are working on a frontend and need to access the backend,
    see the :ref:`backend-api`.


Playback provider
-----------------

.. autoclass:: mopidy.backends.base.BasePlaybackProvider
    :members:
    :undoc-members:


Backend implementations
=======================

* :mod:`mopidy.backends.dummy`
* :mod:`mopidy.backends.libspotify`
* :mod:`mopidy.backends.local`
