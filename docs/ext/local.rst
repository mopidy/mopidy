.. _ext-local:

************
Mopidy-Local
************

Extension for playing music from a local music archive.

This backend handles URIs starting with ``file:``. See
:ref:`music-from-local-storage` for further instructions on using this backend.


Known issues
============

https://github.com/mopidy/mopidy/issues?labels=Local+backend


Dependencies
============

None. The extension just needs Mopidy.


Configuration values
====================

.. confval:: local/enabled

    If the local extension should be enabled or not.

.. confval:: local/media_dir

    Path to directory with local media files.

.. confval:: local/playlists_dir

    Path to playlists directory with m3u files for local media.

.. confval:: local/tag_cache_file

    Path to tag cache for local media.


Default configuration
=====================

.. literalinclude:: ../../mopidy/backends/local/ext.conf
    :language: ini
