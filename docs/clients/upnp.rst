.. _upnp-clients:

************
UPnP clients
************

`UPnP <https://en.wikipedia.org/wiki/Universal_Plug_and_Play>`_ is a set of
specifications for media sharing, playing, remote control, etc, across a home
network. The specs are supported by a lot of consumer devices (like
smartphones, TVs, Xbox, and PlayStation) that are often labeled as being `DLNA
<https://en.wikipedia.org/wiki/DLNA>`_ compatible or certified.

The DLNA guidelines and UPnP specifications defines several device roles, of
which Mopidy may play two:

DLNA Digital Media Server (DMS) / UPnP AV MediaServer:

    A MediaServer provides a library of media and is capable of streaming that
    media to a MediaRenderer. If Mopidy was a MediaServer, you could browse and
    play Mopidy's music on a TV, smartphone, or tablet supporting UPnP. Mopidy
    does not currently support this, but we may in the future. :issue:`52` is
    the relevant wishlist issue.

DLNA Digital Media Renderer (DMR) / UPnP AV MediaRenderer:

    A MediaRenderer is asked by some remote controller to play some
    given media, typically served by a MediaServer. If Mopidy was a
    MediaRenderer, you could use e.g. your smartphone or tablet to make Mopidy
    play media. Mopidy *does already* have experimental support for being a
    MediaRenderer, as you can read more about below.


Mopidy as an UPnP MediaRenderer
===============================

There are two ways Mopidy can be made available as an UPnP MediaRenderer:
Using Mopidy-MPRIS and Rygel, or using Mopidy-MPD and upmpdcli.


Mopidy-MPD and upmpdcli
-----------------------

`upmpdcli <https://www.lesbonscomptes.com/upmpdcli/>`_ is recommended, since it
is easier to setup, and offers `OpenHome
<http://wiki.openhome.org/wiki/OhMedia>`_ compatibility. upmpdcli exposes a UPnP
MediaRenderer to the network, while using the MPD protocol to control Mopidy.

1. Install upmpdcli. On Debian/Ubuntu::

       apt-get install upmpdcli

   Alternatively, follow the instructions from the upmpdcli website.

2. The default settings of upmpdcli will work with the default settings of
   :ref:`ext-mpd`. Edit :file:`/etc/upmpdcli.conf` if you want to use different
   ports, hosts, or other settings.

3. Start upmpdcli using the command::

       upmpdcli

   Or, run it in the background as a service::

       sudo service upmpdcli start

4. A UPnP renderer should be available now.


Mopidy-MPRIS and Rygel
----------------------

See the `Mopidy-MPRIS <https://github.com/mopidy/mopidy-mpris>`_ documentation
for how to setup Rygel to make Mopidy an UPnP MediaRenderer.


Clients
=======

For a long list of UPnP clients for all possible platforms, see Wikipedia's
`List of UPnP AV media servers and clients
<https://en.wikipedia.org/wiki/List_of_UPnP_AV_media_servers_and_clients>`_.
