************************
MPD client compatability
************************

This is a list of MPD clients we either know works well with Mopidy, or that we
know won't work well. For a more exhaustive list of MPD clients, see
http://mpd.wikia.com/wiki/Clients.


Console clients
===============

mpc
---

A command line client. Version 0.14 had some issues with Mopidy (see
:issue:`5`), but 0.16 seems to work nicely.

ncmpc
-----

A console client. Uses the ``idle`` command heavily, which Mopidy doesn't
support yet. If you want a console client, use ncmpcpp instead.

ncmpcpp
-------

A console client that generally works well with Mopidy, and is regularly used
by Mopidy developers.

Search only works for ncmpcpp versions 0.5.1 and higher, and in two of the
three search modes:

- "Match if tag contains search phrase (regexes supported)" -- Does not work.
  The client tries to fetch all known metadata and do the search client side.
- "Match if tag contains searched phrase (no regexes)" -- Works.
- "Match only if both values are the same" -- Works.

If you run Ubuntu 10.04 or older, you can fetch an updated version of ncmpcpp
from `Launchpad <https://launchpad.net/ubuntu/+source/ncmpcpp>`_.


Graphical clients
=================

GMPC
----

A GTK+ client which works well with Mopidy, and is regularly used by Mopidy
developers.

Sonata
------

A GTK+ client. Generally works well with Mopidy.

Search does not work, because they do most of the search on the client side.
See :issue:`1` for details.


Android clients
===============

BitMPC
------

Works well with Mopidy.

Droid MPD
---------

Works well with Mopidy.

MPDroid
-------

Works well with Mopidy, and is regularly used by Mopidy developers.

PMix
----

Works well with Mopidy.

ThreeMPD
--------

Does not work well with Mopidy, because we haven't implemented ``listallinfo``
yet.


iPhone/iPod Touch clients
=========================

impdclient
----------

There's an open source MPD client for iOS called `impdclient
<http://code.google.com/p/impdclient/>`_ which has not seen any updates since
August 2008. So far, we've not heard of users trying it with Mopidy. Please
notify us of your successes and/or problems if you do try it out.

MPod
----

The `MPoD <http://www.katoemba.net/makesnosenseatall/mpod/>`_ client can be
installed from the `iTunes Store
<http://itunes.apple.com/us/app/mpod/id285063020>`_.

Users have reported varying success in using MPoD together with Mopidy. Thus,
we've tested a fresh install of MPoD 1.5.1 with Mopidy as of revision e7ed28d
(pre-0.3) on an iPod Touch 3rd generation. The following are our findings:

- **Works:** Playback control generally works, including stop, play, pause,
  previous, next, repeat, random, seek, and volume control.

- **Bug:** Search does not work, neither in the artist, album, or song
  tabs. Mopidy gets no requests at all from MPoD when executing searches. Seems
  like MPoD only searches in local cache, even if "Use local cache" is turned
  off in MPoD's settings. Until this is fixed by the MPoD developer, MPoD will
  be much less useful with Mopidy.

- **Bug:** When adding another playlist to the current playlist in MPoD,
  the currently playing track restarts at the beginning. I do not currently
  know enough about this bug, because I'm not sure if MPoD was in the "add to
  active playlist" or "replace active playlist" mode when I tested it. I only
  later learned what that button was for. Anyway, what I experienced was:

  #. I play a track
  #. I select a new playlist
  #. MPoD reconnects to Mopidy for unknown reason
  #. MPoD issues MPD command ``load "a playlist name"``
  #. MPoD issues MPD command ``play "-1"``
  #. MPoD issues MPD command ``playlistinfo "-1"``
  #. I hear that the currently playing tracks restarts playback

- **Tips:** MPoD seems to cache stored playlists, but they won't work if the
  server hasn't loaded stored playlists from e.g. Spotify yet. A trick to force
  refetching of playlists from Mopidy is to add a new empty playlist in MPoD.

- **Wishlist:** Modifying the current playlists is not supported by MPoD it
  seems.

- **Wishlist:** MPoD supports playback of Last.fm radio streams through the MPD
  server. Mopidy does not currently support this, but there is a wishlist bug
  at :issue:`38`.

- **Wishlist:** MPoD supports autodetection/-configuration of MPD servers
  through the use of Bonjour. Mopidy does not currently support this, but there
  is a wishlist bug at :issue:`39`.
