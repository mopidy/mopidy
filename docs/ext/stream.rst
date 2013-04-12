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
