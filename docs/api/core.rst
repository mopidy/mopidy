.. _core-api:

********
Core API
********


The core API is the interface that is used by frontends like
:mod:`mopidy.frontends.mpd`. The core layer is inbetween the frontends and the
backends.


Playback controller
===================

Manages playback, with actions like play, pause, stop, next, previous,
seek, and volume control.

.. autoclass:: mopidy.core.PlaybackState
    :members:

.. autoclass:: mopidy.core.PlaybackController
    :members:


Current playlist controller
===========================

Manages everything related to the currently loaded playlist.

.. autoclass:: mopidy.core.CurrentPlaylistController
    :members:


Stored playlists controller
===========================

Manages stored playlist.

.. autoclass:: mopidy.core.StoredPlaylistsController
    :members:


Library controller
==================

Manages the music library, e.g. searching for tracks to be added to a playlist.

.. autoclass:: mopidy.core.LibraryController
    :members:
