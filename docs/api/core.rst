.. _core-api:

********
Core API
********

.. module:: mopidy.core
    :synopsis: Core API for use by frontends

The core API is the interface that is used by frontends like
:mod:`mopidy.http` and :mod:`mopidy.mpd`. The core layer is in between the
frontends and the backends. Don't forget that you will be accessing core
as a Pykka actor.

.. autoclass:: mopidy.core.Core

  .. attribute:: tracklist

    Manages everything related to the list of tracks we will play.
    See :class:`~mopidy.core.TracklistController`.

  .. attribute:: playback

    Manages playback state and the current playing track.
    See :class:`~mopidy.core.PlaybackController`.

  .. attribute:: library

    Manages the music library, e.g. searching and browsing for music.
    See :class:`~mopidy.core.LibraryController`.

  .. attribute:: playlists

    Manages stored playlists. See :class:`~mopidy.core.PlaylistsController`.

  .. attribute:: mixer

    Manages volume and muting. See :class:`~mopidy.core.MixerController`.

  .. attribute:: history

    Keeps record of what tracks have been played.
    See :class:`~mopidy.core.HistoryController`.

  .. automethod:: get_uri_schemes

  .. automethod:: get_version


Tracklist controller
====================

.. autoclass:: mopidy.core.TracklistController

Manipulating
------------

.. automethod:: mopidy.core.TracklistController.add
.. automethod:: mopidy.core.TracklistController.remove
.. automethod:: mopidy.core.TracklistController.clear
.. automethod:: mopidy.core.TracklistController.move
.. automethod:: mopidy.core.TracklistController.shuffle

Current state
-------------

.. automethod:: mopidy.core.TracklistController.get_tl_tracks
.. automethod:: mopidy.core.TracklistController.index
.. automethod:: mopidy.core.TracklistController.get_version

.. automethod:: mopidy.core.TracklistController.get_length
.. automethod:: mopidy.core.TracklistController.get_tracks

.. automethod:: mopidy.core.TracklistController.slice
.. automethod:: mopidy.core.TracklistController.filter

Future state
------------

.. automethod:: mopidy.core.TracklistController.get_eot_tlid
.. automethod:: mopidy.core.TracklistController.get_next_tlid
.. automethod:: mopidy.core.TracklistController.get_previous_tlid

.. automethod:: mopidy.core.TracklistController.eot_track
.. automethod:: mopidy.core.TracklistController.next_track
.. automethod:: mopidy.core.TracklistController.previous_track

Options
-------

.. automethod:: mopidy.core.TracklistController.get_consume
.. automethod:: mopidy.core.TracklistController.set_consume
.. automethod:: mopidy.core.TracklistController.get_random
.. automethod:: mopidy.core.TracklistController.set_random
.. automethod:: mopidy.core.TracklistController.get_repeat
.. automethod:: mopidy.core.TracklistController.set_repeat
.. automethod:: mopidy.core.TracklistController.get_single
.. automethod:: mopidy.core.TracklistController.set_single


Playback controller
===================

Manages playback, with actions like play, pause, stop, next, previous,
seek, and volume control.

.. autoclass:: mopidy.core.PlaybackState
    :members:

.. autoclass:: mopidy.core.PlaybackController
    :members:

History controller
==================

.. autoclass:: mopidy.core.HistoryController
    :members:


Playlists controller
====================

.. autoclass:: mopidy.core.PlaylistsController
    :members:


Library controller
==================

.. autoclass:: mopidy.core.LibraryController
    :members:


Mixer controller
================

.. autoclass:: mopidy.core.MixerController
    :members:

Core listener
=============

.. autoclass:: mopidy.core.CoreListener
    :members:

Deprecated API features
=======================

.. warning::
  Though these features still work, they are slated to go away in the next
  major Mopidy release.

Core
----

.. autoattribute:: mopidy.core.Core.version
.. autoattribute:: mopidy.core.Core.uri_schemes

TracklistController
-------------------

.. autoattribute:: mopidy.core.TracklistController.tl_tracks
.. autoattribute:: mopidy.core.TracklistController.tracks
.. autoattribute:: mopidy.core.TracklistController.version
.. autoattribute:: mopidy.core.TracklistController.length

.. autoattribute:: mopidy.core.TracklistController.consume
.. autoattribute:: mopidy.core.TracklistController.random
.. autoattribute:: mopidy.core.TracklistController.repeat
.. autoattribute:: mopidy.core.TracklistController.single
