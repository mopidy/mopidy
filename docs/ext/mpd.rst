.. _ext-mpd:

**********
Mopidy-MPD
**********

Mopidy-MPD is an extension that provides a full MPD server implementation to
make Mopidy available to :ref:`MPD clients <mpd-clients>`. It is bundled with
Mopidy and enabled by default.

.. warning::

    As a simple security measure, the MPD server is by default only available
    from localhost. To make it available from other computers, change the
    :confval:`mpd/hostname` config value. Before you do so, note that the MPD
    server does not support any form of encryption and only a single clear
    text password (see :confval:`mpd/password`) for weak authentication. Anyone
    able to access the MPD server can control music playback on your computer.
    Thus, you probably only want to make the MPD server available from your
    local network. You have been warned.

MPD stands for Music Player Daemon, which is also the name of the `original MPD
server project <http://mpd.wikia.com/>`_. Mopidy does not depend on the
original MPD server, but implements the MPD protocol itself, and is thus
compatible with clients for the original MPD server.

For more details on our MPD server implementation, see :mod:`mopidy.mpd`.


Limitations
===========

This is a non exhaustive list of MPD features that Mopidy doesn't support.
Items on this list will probably not be supported in the near future.

- Only a single password is supported. It gives all-or-nothing access.
- Toggling of audio outputs is not supported
- Channels for client-to-client communication are not supported
- Stickers are not supported
- Crossfade is not supported
- Replay gain is not supported
- ``stats`` does not provide any statistics
- ``decoders`` does not provide information about available decoders

The following items are currently not supported, but should be added in the
near future:

- ``tagtypes`` is not supported
- Live update of the music database is not supported


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/mpd/ext.conf
    :language: ini

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

.. confval:: mpd/zeroconf

    Name of the MPD service when published through Zeroconf. The variables
    ``$hostname`` and ``$port`` can be used in the name.

    Set to an empty string to disable Zeroconf for MPD.

.. confval:: mpd/command_blacklist

    List of MPD commands which are disabled by the server. By default this
    setting blacklists ``listall`` and ``listallinfo``. These commands don't
    fit well with many of Mopidy's backends and are better left disabled unless
    you know what you are doing.
