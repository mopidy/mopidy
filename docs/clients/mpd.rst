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

Search
^^^^^^

Search only works for ncmpcpp versions 0.5.1 and higher, and in two of the
three search modes:

- "Match if tag contains search phrase (regexes supported)" -- Does not work.
  The client tries to fetch all known metadata and do the search client side.
- "Match if tag contains searched phrase (no regexes)" -- Works.
- "Match only if both values are the same" -- Works.

If you run Ubuntu 10.04 or older, you can fetch an updated version of ncmpcpp
from `Launchpad <https://launchpad.net/ubuntu/+source/ncmpcpp>`_.

Communication mode
^^^^^^^^^^^^^^^^^^

In newer versions of ncmpcpp, like ncmpcpp 0.5.5 shipped with Ubuntu 11.04,
ncmcpp defaults to "notifications" mode for MPD communications, which Mopidy
did not support before Mopidy 0.6. To workaround this limitation in earlier
versions of Mopidy, edit the ncmpcpp configuration file at
``~/.ncmpcpp/config`` and add the following setting::

    mpd_communication_mode = "polling"

If you use Mopidy 0.6 or newer, you don't need to change anything.


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

We've tested all six MPD clients we could find for Android with Mopidy 0.3 on a
HTC Hero with Android 2.1, using the following test procedure:

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

In summary:

- BitMPC lacks finishing touches on its user interface but supports all
  features tested.
- Droid MPD Client works well, but got a couple of bugs one can live with and
  does not expose stored playlist anywhere.
- IcyBeats is not usable yet.
- MPDroid is working well and looking good, but does not have search
  functionality.
- PMix is just a lesser MPDroid, so use MPDroid instead.
- ThreeMPD is too buggy to even get connected to Mopidy.

Our recommendation:

- If you do not care about looks, use BitMPC.
- If you do not care about stored playlists, use Droid MPD Client.
- If you do not care about searching, use MPDroid.


BitMPC
------

We tested version 1.0.0, which at the time had 1k-5k downloads, <100 ratings,
3.5 stars.

The user interface lacks some finishing touches. E.g. you can't enter a
hostname for the server. Only IPv4 addresses are allowed.

All features exercised in the test procedure works. BitMPC lacks support for
single mode and consume mode. BitMPC crashes if Mopidy is killed or crash.


Droid MPD Client
----------------

We tested version 0.4.0, which at the time had 5k-10k downloads, >200 ratings,
4 stars.

To find the search functionality, you have to select the menu, then "Playlist
manager", then the search tab. I do not understand why search is hidden inside
"Playlist manager".

The user interface have some French remnants, like "Rechercher" in the search
field.

When selecting the artist tab, it issues the ``list Artist`` command and
becomes stuck waiting for the results. Same thing happens for the album tab,
which issues ``list Album``, and the folder tab, which issues ``lsinfo``.
Mopidy returned zero hits immediately on all three commands. If Mopidy has
loaded your stored playlists and returns more than zero hits on these commands,
they artist and album tabs do not hang. The folder tab still freezes when
``lsinfo`` returns a list of stored playlists, though zero files. Thus, we've
discovered a couple of bugs in Droid MPD Client.

The volume control is very slick, with a turn knob, just like on an amplifier.
It lends itself to showing off to friends when combined with Mopidy's external
amplifier mixers. Everybody loves turning a knob on a touch screen and see the
physical knob on the amplifier turn as well ;-)

Even though ``lsinfo`` returns the stored playlists for the folder tab, they
are not displayed anywhere. Thus, we had to select an album in the album tab to
complete the test procedure.

At one point, I had problems turning off repeat mode. After I adjusted the
volume and tried again, it worked.

Droid MPD client does not support single mode or consume mode. It does not
detect that the server is killed/crashed. You'll only notice it by no actions
having any effect, e.g. you can't turn the volume knob any more.

In conclusion, some bugs and caveats, but most of the test procedure was
possible to perform.


IcyBeats
--------

We tested version 0.2, which at the time had 50-100 downloads, no ratings.
The app was still in beta when we tried it.

IcyBeats successfully connected to Mopidy and I was able to adjust volume. When
I was searching for some tracks, I could not figure out how to actually start
the search, as there was no search button and pressing enter in the input field
just added a new line. I was stuck. In other words, IcyBeats 0.2 is not usable
with Mopidy.

IcyBeats does have something going for it: IcyBeats uses IPv6 to connect to
Mopidy. The future is just around the corner!


MPDroid
-------

We tested version 0.6.9, which at the time had 5k-10k downloads, <200 ratings,
4.5 stars. MPDroid started out as a fork of PMix.

First of all, MPDroid's user interface looks nice.

I couldn't find any search functionality, so I added the initial track using
another client. Other than the missing search functionality, everything in the
test procedure worked out flawlessly. Like all other Android clients, MPDroid
does not support single mode or consume mode. When Mopidy is killed, MPDroid
handles it gracefully and asks if you want to try to reconnect.

All in all, MPDroid is a good MPD client without search support.


PMix
----

We tested version 0.4.0, which at the time had 10k-50k downloads, >200 ratings,
4 stars.

Add MPDroid is a fork from PMix, it is no surprise that PMix does not support
search either. In addition, I could not find stored playlists. Other than that,
I was able to complete the test procedure. PMix crashed once during testing,
but handled the killing of Mopidy just as nicely as MPDroid. It does not
support single mode or consume mode.

All in all, PMix works but can do less than MPDroid. Use MPDroid instead.


ThreeMPD
--------

We tested version 0.3.0, which at the time had 1k-5k downloads, <25 ratings,
2.5 average. The developer request users to use MPDroid instead, due to limited
time for maintenance. Does not support password authentication.

ThreeMPD froze during startup, so we were not able to test it.


.. _ios_mpd_clients:

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
