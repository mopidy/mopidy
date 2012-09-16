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

A console client. Works with Mopidy 0.6 and upwards. Uses the ``idle`` MPD
command, but in a resource inefficient way.


ncmpcpp
-------

A console client that generally works well with Mopidy, and is regularly used
by Mopidy developers.

Search only works in two of the three search modes:

- "Match if tag contains search phrase (regexes supported)" -- Does not work.
  The client tries to fetch all known metadata and do the search client side.
- "Match if tag contains searched phrase (no regexes)" -- Works.
- "Match only if both values are the same" -- Works.


Graphical clients
=================

GMPC
----

`GMPC <http://gmpc.wikia.com>`_ is a graphical MPD client (GTK+) which works
well with Mopidy, and is regularly used by Mopidy developers.

GMPC may sometimes requests a lot of meta data of related albums, artists, etc.
This takes more time with Mopidy, which needs to query Spotify for the data,
than with a normal MPD server, which has a local cache of meta data. Thus, GMPC
may sometimes feel frozen, but usually you just need to give it a bit of slack
before it will catch up.


Sonata
------

`Sonata <http://sonata.berlios.de/>`_ is a graphical MPD client (GTK+).
It generally works well with Mopidy, except for search.

When you search in Sonata, it only sends the first to letters of the search
query to Mopidy, and then does the rest of the filtering itself on the client
side. Since Spotify has a collection of millions of tracks and they only return
the first 100 hits for any search query, searching for two-letter combinations
seldom returns any useful results. See :issue:`1` and the matching `Sonata
bug`_ for details.

.. _Sonata bug: http://developer.berlios.de/feature/?func=detailfeature&feature_id=5038&group_id=7323


Theremin
--------

`Theremin <http://theremin.sigterm.eu/>`_ is a graphical MPD client for OS X.
It generally works well with Mopidy.


.. _android_mpd_clients:

Android clients
===============

We've tested all four MPD clients we could find for Android with Mopidy 0.7.3 on
a Samsung Galaxy Nexus with Android 4.1.1, using the following test procedure:

#. Connect to Mopidy
#. Search for ``foo``, with search type "any" if it can be selected
#. Add "The Pretender" from the search results to the current playlist
#. Start playback
#. Pause and resume playback
#. Adjust volume
#. Find a playlist and append it to the current playlist
#. Skip to next track
#. Skip to previous track
#. Select the last track from the current playlist
#. Turn on repeat mode
#. Seek to 10 seconds or so before the end of the track
#. Wait for the end of the track and confirm that playback continues at the
   start of the playlist
#. Turn off repeat mode
#. Turn on random mode
#. Skip to next track and confirm that it random mode works
#. Turn off random mode
#. Stop playback
#. Check if the app got support for single mode and consume mode
#. Kill Mopidy and confirm that the app handles it without crashing

We found that all four apps crashed on Android 4.1.1.

Combining what we managed to find before the apps crashed with our experience
from an older version of this review, using Android 2.1, we can say that:

- PMix can be ignored, because it is unmaintained and its fork MPDroid is
  better on all fronts.

- Droid MPD Client was to buggy to get an impression from. Unclear if the bugs
  are due to the app or that it hasn't been updated for Android 4.x.

- BitMPC is in our experience feature complete, but ugly.

- MPDroid, now that search is in place, is probably feature complete as well,
  and looks nicer than BitMPC.

In conclusion: MPD clients on Android 4.x is a sad affair. If you want to try
anyway, try BitMPC and MPDroid.


BitMPC
------

Test date:
    2012-09-12
Tested version:
    1.0.0 (released 2010-04-12)
Downloads:
    5,000+
Rating:
    3.7 stars from about 100 ratings


- The user interface lacks some finishing touches. E.g. you can't enter a
  hostname for the server. Only IPv4 addresses are allowed.

- When we last tested the same version of BitMPC using Android 2.1:

  - All features exercised in the test procedure worked.

  - BitMPC lacked support for single mode and consume mode.

  - BitMPC crashed if Mopidy was killed or crashed.

- When we tried to test using Android 4.1.1, BitMPC started and connected to
  Mopidy without problems, but the app crashed as soon as fire off our search,
  and continued to crash on startup after that.

In conclusion, BitMPC is usable if you got an older Android phone and don't
care about looks. For newer Android versions, BitMPC will probably not work as
it hasn't been maintained for 2.5 years.


Droid MPD Client
----------------

Test date:
    2012-09-12
Tested version:
    1.4.0 (released 2011-12-20)
Downloads:
    10,000+
Rating:
    4.2 stars from 400+ ratings

- No intutive way to ask the app to connect to the server after adding the
  server hostname to the settings.

- To find the search functionality, you have to select the menu,
  then "Playlist manager", then the search tab. I do not understand why search
  is hidden inside "Playlist manager".

- The tabs "Artists" and "Albums" did not contain anything, and did not cause
  any requests.

- The tab "Folders" showed a spinner and said "Updating data..." but did not
  send any requests.

- Searching for "foo" did nothing. No request was sent to the server.

- Once, I managed to get a list of stored playlists in the "Search" tab, but I
  never managed to reproduce this. Opening the stored playlists doesn't work,
  because Mopidy haven't implemented ``lsinfo "Playlist name"`` (see
  :issue:`193`).

- Droid MPD client does not support single mode or consume mode.

- Not able to complete the test procedure, due to the above problems.

In conclusion, not a client we can recommend.


MPDroid
-------

Test date:
    2012-09-12
Tested version:
    0.7 (released 2011-06-19)
Downloads:
    10,000+
Rating:
    4.5 stars from ~500 ratings

- MPDroid started out as a fork of PMix.

- First of all, MPDroid's user interface looks nice.

- Last time we tested MPDroid (v0.6.9), we couldn't find any search
  functionality. Now we found it, and it worked.

- Last time we tested MPDroid (v0.6.9) everything in the test procedure worked
  out flawlessly.

- Like all other Android clients, MPDroid does not support single mode or
  consume mode.

- When Mopidy is killed, MPDroid handles it gracefully and asks if you want to
  try to reconnect.

- When using Android 4.1.1, MPDroid crashes here and there, e.g. when having an
  empty current playlist and pressing play.

Disregarding Android 4.x problems, MPDroid is a good MPD client.


PMix
----

Test date:
    2012-09-12
Tested version:
    0.4.0 (released 2010-03-06)
Downloads:
    10,000+
Rating:
    3.8 stars from >200 ratings

- Using Android 4.1.1, PMix, which haven't been updated for 2.5 years, crashes
  as soon as it connects to Mopidy.

- Last time we tested the same version of PMix using Android 2.1, we found
  that:

  - PMix does not support search.

  - I could not find stored playlists.

  - Other than that, I was able to complete the test procedure.

  - PMix crashed once during testing.

  - PMix handled the killing of Mopidy just as nicely as MPDroid.

  - It does not support single mode or consume mode.

All in all, PMix works but can do less than MPDroid. Use MPDroid instead.


.. _ios_mpd_clients:

iOS clients
===========

MPod
----

Test date:
    2011-01-19
Tested version:
    1.5.1

The `MPoD <http://www.katoemba.net/makesnosenseatall/mpod/>`_ iPhone/iPod Touch
app can be installed from the `iTunes Store
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


MPaD
----

The `MPaD <http://www.katoemba.net/makesnosenseatall/mpad/>`_ iPad app works
with Mopidy. A complete review may appear here in the future.
