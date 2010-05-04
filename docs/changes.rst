*******
Changes
*******

This change log is used to track all major changes to Mopidy.

0.1.0a1 (unreleased)
====================

- Backend API changes:

    - Removed ``backend.playback.volume`` wrapper. Use ``backend.mixer.volume``
      directly.
    - Renamed ``backend.playback.playlist_position`` to
      ``current_playlist_position`` to match naming of ``current_track``.
    - **[WIP]** Changed API for get/filter/find_exact/search.

- **[WIP]** Merged the ``gstreamer`` branch from Thomas Adamcik:

    - More than 200 new tests, and thus several bugfixes to existing code.
    - Several new generic features, like shuffle, consume, and playlist repeat.
    - A new backend for playing music from a local music archive using the
      Gstreamer library.

- Made :class:`mopidy.mixers.alsa.AlsaMixer` work on machines without a mixer
  named "Master".
- Make :class:`mopidy.backends.DespotifyBackend` ignore local files in
  playlists (feature added in Spotify 0.4.3). Reported by Richard Haugen Olsen.


0.1.0a0 (2010-03-27)
====================

"*Release early. Release often. Listen to your customers.*" wrote Eric S.
Raymond in *The Cathedral and the Bazaar*.

Three months of development should be more than enough. We have more to do, but
Mopidy is working and usable. 0.1.0a0 is an alpha release, which basicly means
we will still change APIs, add features, etc. before the final 0.1.0 release.
But the software is usable as is, so we release it. Please give it a try and
give us feedback, either at our IRC channel or through the `issue tracker
<http://github.com/jodal/mopidy/issues>`_. Thanks!

**Changes**

- Initial version. No changelog available.
