.. _ext-stream:

*************
Mopidy-Stream
*************

Mopidy-Stream is an extension for playing streaming music. It is bundled with
Mopidy and enabled by default.

This backend does not provide a library or playlist storage. It simply accepts
any URI added to Mopidy's tracklist that matches any of the protocols in the
:confval:`stream/protocols` config value. It then tries to retrieve metadata
and play back the URI using GStreamer. For example, if you're using an MPD
client, you'll just have to find your clients "add URI" interface, and provide
it with the URI of a stream.

In addition to playing streams, the extension also understands how to extract
streams from a lot of playlist formats. This is convenient as most Internet
radio stations links to playlists instead of directly to the radio streams.

If you're having trouble playing back a stream, run the ``mopidy deps``
command to check if you have all relevant GStreamer plugins installed.


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/stream/ext.conf
    :language: ini

.. confval:: stream/enabled

    If the stream extension should be enabled or not.

.. confval:: stream/protocols

    Whitelist of URI schemas to allow streaming from. Values should be
    separated by either comma or newline.

.. confval:: stream/timeout

    Number of milliseconds before giving up looking up stream metadata.

.. confval:: stream/metadata_blacklist

    List of URI globs to not fetch metadata from before playing. This feature
    is typically needed for play once URIs provided by certain streaming
    providers. Regular POSIX glob semantics apply, so ``http://*.example.com/*``
    would match all example.com sub-domains.
