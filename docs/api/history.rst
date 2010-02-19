History handling
================

For correct logical handling of ``previous()`` and ``previous_track`` backends
will need to keep track of which songs they have played.

Normal playback
----------------

Each time a new song is played the previous ``current_track`` should be added to
the history. The ``previous_track`` should always be the most recent history item.

Playback with repeat enabled
-----------------------------

History should be handled in same manner as regular playback. ``next_track``
at end of playlist should loop to first item on playlist.

Playback with random enabled
-----------------------------

Each song should only be played once until entire playlist has been played,
once this has occurred a new random order should be played. History should be
handled in the same way as regular playback.

A suggested implementation is creating a shuffled copy of the tracks and
retrieving ``next_track`` from here until it is empty.

Playback with consume enabled
-----------------------------

Turning on consume should set history to an empty array, and not add any new
tracks while it is on. ``previous_track`` should return ``current_track`` to
match MPD behaviour.

Playback with repeat and random
-------------------------------

Once the shuffled tracks array is empty it should be replaced with a new
shuffled array of tracks.

Playback with repeat and consume
--------------------------------

Return ``current_track`` for ``previous_track`` to match MPD.

Playback with random and consume
--------------------------------

Return ``current_track`` for ``previous_track`` to match MPD.

Playback with repeat, random and consume
----------------------------------------

Return ``current_track`` for ``previous_track`` to match MPD.
