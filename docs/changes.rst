*******
Changes
*******

This change log is used to track all major changes to Mopidy.

0.1.0a1 (2010-05-04)
====================

Since the previous release Mopidy has seen about 300 commits, more than 200 new
tests, a libspotify release, and major feature additions to Spotify. The new
releases from Spotify have lead to updates to our dependencies, and also to new
bugs in Mopidy. Thus, this is primarily a bugfix release, even though the not
yet finished work on a Gstreamer backend have been merged.

All users are recommended to upgrade to 0.1.0a1, and should at the same time
ensure that they have the latest versions of our dependencies: Despotify r508
if you are using DespotifyBackend, and pyspotify 1.1 with libspotify 0.0.4 if
you are using LibspotifyBackend.

As always, report problems at our IRC channel or our issue tracker. Thanks!

**Changes**

- Backend API changes:

    - Removed ``backend.playback.volume`` wrapper. Use ``backend.mixer.volume``
      directly.
    - Renamed ``backend.playback.playlist_position`` to
      ``current_playlist_position`` to match naming of ``current_track``.
    - Replaced ``get_by_id()`` with a more flexible ``get(**criteria)``.

- Merged the ``gstreamer`` branch from Thomas Adamcik:

    - More than 200 new tests, and thus several bugfixes to existing code.
    - Several new generic features, like shuffle, consume, and playlist repeat.
      (Fixes: GH-3)
    - **[Work in Progress]** A new backend for playing music from a local music
      archive using the Gstreamer library.

- Made :class:`mopidy.mixers.alsa.AlsaMixer` work on machines without a mixer
  named "Master".
- Make :class:`mopidy.backends.DespotifyBackend` ignore local files in
  playlists (feature added in Spotify 0.4.3). Reported by Richard Haugen Olsen.
- And much more.


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
