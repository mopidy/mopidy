.. _core-api:

*******************************
:mod:`mopidy.core` --- Core API
*******************************

.. module:: mopidy.core
    :synopsis: Core API for use by frontends

The core API is the interface that is used by frontends like
:mod:`mopidy.http` and :mod:`mopidy.mpd`. The core layer is in between the
frontends and the backends. Don't forget that you will be accessing core
as a Pykka actor. If you are only interested in being notified about changes
in core see :class:`~mopidy.core.CoreListener`.

.. versionchanged:: 1.1
    All core API calls are now type checked.

.. versionchanged:: 1.1
    All backend return values are now type checked.

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

.. autoclass:: mopidy.core.PlaybackController

Playback control
----------------

.. automethod:: mopidy.core.PlaybackController.play
.. automethod:: mopidy.core.PlaybackController.next
.. automethod:: mopidy.core.PlaybackController.previous
.. automethod:: mopidy.core.PlaybackController.stop
.. automethod:: mopidy.core.PlaybackController.pause
.. automethod:: mopidy.core.PlaybackController.resume
.. automethod:: mopidy.core.PlaybackController.seek

Current track
-------------

.. automethod:: mopidy.core.PlaybackController.get_current_tl_track
.. automethod:: mopidy.core.PlaybackController.get_current_track
.. automethod:: mopidy.core.PlaybackController.get_stream_title
.. automethod:: mopidy.core.PlaybackController.get_time_position

Playback states
---------------

.. automethod:: mopidy.core.PlaybackController.get_state
.. automethod:: mopidy.core.PlaybackController.set_state

.. class:: mopidy.core.PlaybackState

  .. attribute:: STOPPED
    :annotation: = 'stopped'
  .. attribute:: PLAYING
    :annotation: = 'playing'
  .. attribute:: PAUSED
    :annotation: = 'paused'

Library controller
==================

.. class:: mopidy.core.LibraryController

.. automethod:: mopidy.core.LibraryController.browse
.. automethod:: mopidy.core.LibraryController.search
.. automethod:: mopidy.core.LibraryController.lookup
.. automethod:: mopidy.core.LibraryController.refresh
.. automethod:: mopidy.core.LibraryController.get_images
.. automethod:: mopidy.core.LibraryController.get_distinct

Playlists controller
====================

.. class:: mopidy.core.PlaylistsController

.. automethod:: mopidy.core.PlaylistsController.get_uri_schemes

Fetching
--------

.. automethod:: mopidy.core.PlaylistsController.as_list
.. automethod:: mopidy.core.PlaylistsController.get_items
.. automethod:: mopidy.core.PlaylistsController.lookup
.. automethod:: mopidy.core.PlaylistsController.refresh

Manipulating
------------

.. automethod:: mopidy.core.PlaylistsController.create
.. automethod:: mopidy.core.PlaylistsController.save
.. automethod:: mopidy.core.PlaylistsController.delete

Mixer controller
================

.. class:: mopidy.core.MixerController

.. automethod:: mopidy.core.MixerController.get_mute
.. automethod:: mopidy.core.MixerController.set_mute
.. automethod:: mopidy.core.MixerController.get_volume
.. automethod:: mopidy.core.MixerController.set_volume

History controller
==================

.. class:: mopidy.core.HistoryController

.. automethod:: mopidy.core.HistoryController.get_history
.. automethod:: mopidy.core.HistoryController.get_length

Core events
===========

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

PlaybackController
------------------

.. automethod:: mopidy.core.PlaybackController.get_mute
.. automethod:: mopidy.core.PlaybackController.get_volume

.. autoattribute:: mopidy.core.PlaybackController.current_tl_track
.. autoattribute:: mopidy.core.PlaybackController.current_track
.. autoattribute:: mopidy.core.PlaybackController.state
.. autoattribute:: mopidy.core.PlaybackController.time_position
.. autoattribute:: mopidy.core.PlaybackController.mute
.. autoattribute:: mopidy.core.PlaybackController.volume

LibraryController
-----------------

.. automethod:: mopidy.core.LibraryController.find_exact

PlaylistsController
-------------------

.. automethod:: mopidy.core.PlaylistsController.filter
.. automethod:: mopidy.core.PlaylistsController.get_playlists

.. autoattribute:: mopidy.core.PlaylistsController.playlists
