.. _mpd-clients:

***********
MPD clients
***********

This is a list of MPD clients we either know works well with Mopidy, or that we
know won't work well. For a more exhaustive list of MPD clients, see
http://mpd.wikia.com/wiki/Clients.

.. contents:: Contents
    :local:


Test procedure
==============

In some cases, we've used the following test procedure to compare the feature
completeness of clients:

#. Connect to Mopidy
#. Search for "foo", with search type "any" if it can be selected
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



Console clients
===============

ncmpcpp
-------

A console client that works well with Mopidy, and is regularly used by Mopidy
developers.

.. image:: mpd-client-ncmpcpp.png
    :width: 575
    :height: 426

Search does not work in the "Match if tag contains search phrase (regexes
supported)" mode because the client tries to fetch all known metadata and do
the search on the client side. The two other search modes works nicely, so this
is not a problem.


ncmpc
-----

A console client. Works with Mopidy 0.6 and upwards. Uses the ``idle`` MPD
command, but in a resource inefficient way.


mpc
---

A command line client. Version 0.16 and upwards seems to work nicely with
Mopidy.


Graphical clients
=================

GMPC
----

`GMPC <http://gmpc.wikia.com>`_ is a graphical MPD client (GTK+) which works
well with Mopidy.

.. image:: mpd-client-gmpc.png
    :width: 1000
    :height: 565

GMPC may sometimes requests a lot of meta data of related albums, artists, etc.
This takes more time with Mopidy, which needs to query Spotify for the data,
than with a normal MPD server, which has a local cache of meta data. Thus, GMPC
may sometimes feel frozen, but usually you just need to give it a bit of slack
before it will catch up.


Sonata
------

`Sonata <http://sonata.berlios.de/>`_ is a graphical MPD client (GTK+).
It generally works well with Mopidy, except for search.

.. image:: mpd-client-sonata.png
    :width: 475
    :height: 424

When you search in Sonata, it only sends the first to letters of the search
query to Mopidy, and then does the rest of the filtering itself on the client
side. Since Spotify has a collection of millions of tracks and they only return
the first 100 hits for any search query, searching for two-letter combinations
seldom returns any useful results. See :issue:`1` and the closed `Sonata bug`_
for details.

.. _Sonata bug: http://developer.berlios.de/feature/?func=detailfeature&feature_id=5038&group_id=7323


Theremin
--------

`Theremin <https://github.com/pweiskircher/Theremin>`_ is a graphical MPD
client for OS X. It is unmaintained, but generally works well with Mopidy.


.. _android_mpd_clients:

Android clients
===============

We've tested all five MPD clients we could find for Android with Mopidy 0.8.1
on a Samsung Galaxy Nexus with Android 4.1.2, using our standard test
procedure.


MPDroid
-------

Test date:
    2012-11-06
Tested version:
    1.03.1 (released 2012-10-16)

.. image:: mpd-client-mpdroid.jpg
    :width: 288
    :height: 512

You can get `MPDroid from Google Play
<https://play.google.com/store/apps/details?id=com.namelessdev.mpdroid>`_.

- MPDroid started out as a fork of PMix, and is now much better.

- MPDroid's user interface looks nice.

- Everything in the test procedure works.

- In contrast to all other Android clients, MPDroid does support single mode or
  consume mode.

- When Mopidy is killed, MPDroid handles it gracefully and asks if you want to
  try to reconnect.

MPDroid is a good MPD client, and really the only one we can recommend.


BitMPC
------

Test date:
    2012-11-06
Tested version:
    1.0.0 (released 2010-04-12)

You can get `BitMPC from Google Play
<https://play.google.com/store/apps/details?id=bitendian.bitmpc>`_.

- The user interface lacks some finishing touches. E.g. you can't enter a
  hostname for the server. Only IPv4 addresses are allowed.

- When we last tested the same version of BitMPC using Android 2.1:

  - All features exercised in the test procedure worked.

  - BitMPC lacked support for single mode and consume mode.

  - BitMPC crashed if Mopidy was killed or crashed.

- When we tried to test using Android 4.1.1, BitMPC started and connected to
  Mopidy without problems, but the app crashed as soon as we fired off our
  search, and continued to crash on startup after that.

In conclusion, BitMPC is usable if you got an older Android phone and don't
care about looks. For newer Android versions, BitMPC will probably not work as
it hasn't been maintained for 2.5 years.


Droid MPD Client
----------------

Test date:
    2012-11-06
Tested version:
    1.4.0 (released 2011-12-20)

You can get `Droid MPD Client from Google Play
<https://play.google.com/store/apps/details?id=com.soreha.droidmpdclient>`_.

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

- Droid MPD client does not support single mode or consume mode.

- Not able to complete the test procedure, due to the above problems.

In conclusion, not a client we can recommend.


PMix
----

Test date:
    2012-11-06
Tested version:
    0.4.0 (released 2010-03-06)

You can get `PMix from Google Play
<https://play.google.com/store/apps/details?id=org.pmix.ui>`_.

PMix haven't been updated for 2.5 years, and has less working features than
it's fork MPDroid. Ignore PMix and use MPDroid instead.


MPD Remote
----------

Test date:
    2012-11-06
Tested version:
    1.0 (released 2012-05-01)

You can get `MPD Remote from Google Play
<https://play.google.com/store/apps/details?id=fr.mildlyusefulsoftware.mpdremote>`_.

This app looks terrible in the screen shots, got just 100+ downloads, and got a
terrible rating. I honestly didn't take the time to test it.


.. _ios_mpd_clients:

iOS clients
===========

MPoD
----

Test date:
    2012-11-06
Tested version:
    1.7.1

.. image:: mpd-client-mpod.jpg
    :width: 320
    :height: 480

The `MPoD <http://www.katoemba.net/makesnosenseatall/mpod/>`_ iPhone/iPod Touch
app can be installed from `MPoD at iTunes Store
<https://itunes.apple.com/us/app/mpod/id285063020>`_.

- The user interface looks nice.

- All features exercised in the test procedure worked with MPaD, except seek,
  which I didn't figure out to do.

- Search only works in the "Browse" tab, and not under in the "Artist",
  "Album", or "Song" tabs. For the tabs where search doesn't work, no queries
  are sent to Mopidy when searching.

- Single mode and consume mode is supported.


MPaD
----

Test date:
    2012-11-06
Tested version:
    1.7.1

.. image:: mpd-client-mpad.jpg
    :width: 480
    :height: 360

The `MPaD <http://www.katoemba.net/makesnosenseatall/mpad/>`_ iPad app can be
purchased from `MPaD at iTunes Store
<https://itunes.apple.com/us/app/mpad/id423097706>`_

- The user interface looks nice, though I would like to be able to view the
  current playlist in the large part of the split view.

- All features exercised in the test procedure worked with MPaD.

- Search only works in the "Browse" tab, and not under in the "Artist",
  "Album", or "Song" tabs. For the tabs where search doesn't work, no queries
  are sent to Mopidy when searching.

- Single mode and consume mode is supported.

- The server menu can be very slow top open, and there is no visible feedback
  when waiting for the connection to a server to succeed.


.. _mpd-web-clients:

Web clients
===========

The following web clients use the MPD protocol to communicate with Mopidy. For
other web clients, see :ref:`http-clients`.


Rompr
-----

.. image:: rompr.png
    :width: 557
    :height: 600

`Rompr <http://sourceforge.net/projects/rompr/>`_ is a web based MPD client.
`mrvanes <https://github.com/mrvanes>`_, a Mopidy and Rompr user, said: "These
projects are a real match made in heaven."


Partify
-------

`Partify <http://www.partify.us/>`_ is a web based MPD client focusing on
making music playing collaborative and social.
