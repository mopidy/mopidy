.. _ext-mpd:

**********
Mopidy-MPD
**********

This extension implements an MPD server to make Mopidy available to :ref:`MPD
clients <mpd-clients>`.

MPD stands for Music Player Daemon, which is also the name of the `original MPD
server project <http://mpd.wikia.com/>`_. Mopidy does not depend on the
original MPD server, but implements the MPD protocol itself, and is thus
compatible with clients for the original MPD server.

For more details on our MPD server implementation, see
:mod:`mopidy.frontends.mpd`.


Known issues
============

https://github.com/mopidy/mopidy/issues?labels=MPD+frontend


Limitations
===========

This is a non exhaustive list of MPD features that Mopidy doesn't support.
Items on this list will probably not be supported in the near future.

- Toggling of audio outputs is not supported
- Channels for client-to-client communication are not supported
- Stickers are not supported
- Crossfade is not supported
- Replay gain is not supported
- ``count`` does not provide any statistics
- ``stats`` does not provide any statistics
- ``list`` does not support listing tracks by genre
- ``decoders`` does not provide information about available decoders

The following items are currently not supported, but should be added in the
near future:

- Modifying stored playlists is not supported
- ``tagtypes`` is not supported
- Browsing the file system is not supported
- Live update of the music database is not supported


Dependencies
============

None. The extension just needs Mopidy.


Default configuration
=====================

.. literalinclude:: ../../mopidy/frontends/mpd/ext.conf
    :language: ini


Configuration values
====================

.. confval:: mpd/enabled

    If the MPD extension should be enabled or not.

.. confval:: mpd/hostname

    Which address the MPD server should bind to.

    ``127.0.0.1``
        Listens only on the IPv4 loopback interface
    ``::1``
        Listens only on the IPv6 loopback interface
    ``0.0.0.0``
        Listens on all IPv4 interfaces
    ``::``
        Listens on all interfaces, both IPv4 and IPv6

.. confval:: mpd/port

    Which TCP port the MPD server should listen to.

.. confval:: mpd/password

    The password required for connecting to the MPD server. If blank, no
    password is required.

.. confval:: mpd/max_connections

    The maximum number of concurrent connections the MPD server will accept.

.. confval:: mpd/connection_timeout

    Number of seconds an MPD client can stay inactive before the connection is
    closed by the server.


Usage
=====

The extension is enabled by default. To connect to the server, use an :ref:`MPD
client <mpd-clients>`.


.. _use-mpd-on-a-network:

Connecting from other machines on the network
---------------------------------------------

As a secure default, Mopidy only accepts connections from ``localhost``. If you
want to open it for connections from other machines on your network, see
the documentation for the :confval:`mpd/hostname` config value.

If you open up Mopidy for your local network, you should consider turning on
MPD password authentication by setting the :confval:`mpd/password` config value
to the password you want to use.  If the password is set, Mopidy will require
MPD clients to provide the password before they can do anything else. Mopidy
only supports a single password, and do not support different permission
schemes like the original MPD server.
