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

  .. automethod:: get_uri_schemes

  .. automethod:: get_version

  .. autoattribute:: tracklist
    :annotation:

  .. autoattribute:: playback
    :annotation:

  .. autoattribute:: library
    :annotation:

  .. autoattribute:: playlists
    :annotation:

  .. autoattribute:: mixer
    :annotation:

  .. autoattribute:: history
    :annotation:


Tracklist controller
====================

.. autoclass:: mopidy.core.TracklistController

Manages everything related to the tracks we are currently playing. This is
likely where you need to start as only tracks that are in the *tracklist* can be
played.

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

Keeps record of what tracks have been played.

.. autoclass:: mopidy.core.HistoryController
    :members:


Playlists controller
====================

Manages persistence of playlists.

.. autoclass:: mopidy.core.PlaylistsController
    :members:


Library controller
==================

Manages the music library, e.g. searching for tracks to be added to a playlist.

.. autoclass:: mopidy.core.LibraryController
    :members:


Mixer controller
================

Manages volume and muting.

.. autoclass:: mopidy.core.MixerController
    :members:

Core listener
=============

.. autoclass:: mopidy.core.CoreListener
    :members:

Deprecated API features
=======================

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
