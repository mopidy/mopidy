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


upmpdcli
--------

`upmpdcli <http://www.lesbonscomptes.com/upmpdcli/>`_ is recommended, since it
is easier to setup, and offers `OpenHome 
<http://www.openhome.org/wiki/OhMedia>`_ compatibility. upmpdcli exposes a UPnP
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


Rygel
-----

With the help of `the Rygel project <https://live.gnome.org/Rygel>`_ Mopidy can
be made available as an UPnP MediaRenderer. Rygel will interface with the MPRIS
interface provided by the `Mopidy-MPRIS extension
<https://github.com/mopidy/mopidy-mpris>`_, and make Mopidy available as a
MediaRenderer on the local network. Since this depends on the MPRIS frontend,
which again depends on D-Bus being available, this will only work on Linux, and
not OS X. MPRIS/D-Bus is only available to other applications on the same
host, so Rygel must be running on the same machine as Mopidy.

1. Start Mopidy and make sure the MPRIS frontend is working. It is activated
   by default when the Mopidy-MPRIS extension is installed, but you may miss
   dependencies or be using OS X, in which case it will not work. Check the
   console output when Mopidy is started for any errors related to the MPRIS
   frontend. If you're unsure it is working, there are instructions for how to
   test it in the `Mopidy-MPRIS readme
   <https://github.com/mopidy/mopidy-mpris>`_.

2. Install Rygel. On Debian/Ubuntu::

       sudo apt-get install rygel

3. Enable Rygel's MPRIS plugin. On Debian/Ubuntu, edit ``/etc/rygel.conf``,
   find the ``[MPRIS]`` section, and change ``enabled=false`` to
   ``enabled=true``.

4. Start Rygel by running::

       rygel

   Example output::

       $ rygel
       Rygel-Message: New plugin 'MediaExport' available
       Rygel-Message: New plugin 'org.mpris.MediaPlayer2.mopidy' available

   In the above example, you can see that Rygel found Mopidy, and it is now
   making Mopidy available through Rygel.


The UPnP-Inspector client
=========================

`UPnP-Inspector <http://coherence.beebits.net/wiki/UPnP-Inspector>`_ is a
graphical analyzer and debugging tool for UPnP services. It will detect any
UPnP devices on your network, and show these in a tree structure. This is not a
tool for your everyday music listening while relaxing on the couch, but it may
be of use for testing that your setup works correctly.

1. Install UPnP-Inspector. On Debian/Ubuntu::

       sudo apt-get install upnp-inspector

2. Run it::

       upnp-inspector

3. Assuming that Mopidy is running with a working MPRIS frontend, and that
   Rygel is running on the same machine, Mopidy should now appear in
   UPnP-Inspector's device list.

4. If you expand the tree item saying ``Mopidy
   (MediaRenderer:2)`` or similiar, and then the sub element named
   ``AVTransport:2`` or similar, you'll find a list of commands you can invoke.
   E.g. if you double-click the ``Pause`` command, you'll get a new window
   where you can press an ``Invoke`` button, and then Mopidy should be paused.

Note that if you have a firewall on the host running Mopidy and Rygel, and you
want this to be exposed to the rest of your local network, you need to open up
your firewall for UPnP traffic. UPnP use UDP port 1900 as well as some
dynamically assigned ports. I've only verified that this procedure works across
the network by temporarily disabling the firewall on the the two hosts
involved, so I'll leave any firewall configuration as an exercise to the
reader.


Other clients
=============

For a long list of UPnP clients for all possible platforms, see Wikipedia's
`List of UPnP AV media servers and clients
<https://en.wikipedia.org/wiki/List_of_UPnP_AV_media_servers_and_clients>`_.
