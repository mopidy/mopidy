************************
MPD client compatability
************************

This is a list of MPD clients we either know works well with Mopidy, or that we
know won't work well. For a more exhaustive list of MPD clients, see
http://mpd.wikia.com/wiki/Clients.


Console clients
===============

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

MPod
----

Works well with Mopidy as far as we've heard from users.
