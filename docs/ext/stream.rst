.. _ext-stream:

*************
Mopidy-Stream
*************

Extension for playing streaming music.

The stream backend will handle streaming of URIs matching the
:confval:`stream/protocols` config value, assuming the needed GStreamer plugins
are installed.


Known issues
============

https://github.com/mopidy/mopidy/issues?labels=Stream+backend


Dependencies
============

None. The extension just needs Mopidy.


Default configuration
=====================

.. literalinclude:: ../../mopidy/backends/stream/ext.conf
    :language: ini


Configuration values
====================

.. confval:: stream/enabled

    If the stream extension should be enabled or not.

.. confval:: stream/protocols

    Whitelist of URI schemas to allow streaming from.


Usage
=====

This backend does not provide a library or similar. It simply takes any URI
added to Mopidy's tracklist that matches any of the protocols in the
:confval:`stream/protocols` setting and tries to play back the URI using
GStreamer. E.g. if you're using an MPD client, you'll just have to find your
clients "add URI" interface, and provide it with the direct URI of the stream.

Currently the stream backend can only work with URIs pointing direcly at
streams, and not intermediate playlists which is often used. See :issue:`303`
to track the development of playlist expansion support.
