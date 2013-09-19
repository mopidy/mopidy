.. _ext-local:

************
Mopidy-Local
************

Extension for playing music from a local music archive.

This backend handles URIs starting with ``file:``.


Known issues
============

https://github.com/mopidy/mopidy/issues?labels=Local+backend


Dependencies
============

None. The extension just needs Mopidy.


Default configuration
=====================

.. literalinclude:: ../../mopidy/backends/local/ext.conf
    :language: ini


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

.. confval:: local/scan_timeout

    Number of milliseconds before giving up scanning a file and moving on to
    the next file.


Usage
=====

If you want use Mopidy to play music you have locally at your machine, you need
to review and maybe change some of the local extension config values. See above
for a complete list. Then you need to generate a tag cache for your local
music...


.. _generating-a-tag-cache:

Generating a tag cache
----------------------

The program :command:`mopidy-scan` will scan the path set in the
:confval:`local/media_dir` config value for any media files and build a MPD
compatible ``tag_cache``.

To make a ``tag_cache`` of your local music available for Mopidy:

#. Ensure that the :confval:`local/media_dir` config value points to where your
   music is located. Check the current setting by running::

    mopidy --show-config

#. Scan your media library. The command outputs the ``tag_cache`` to
   standard output, which means that you will need to redirect the output to a
   file yourself::

    mopidy-scan > tag_cache

#. Move the ``tag_cache`` file to the location
   set in the :confval:`local/tag_cache_file` config value, or change the
   config value to point to where your ``tag_cache`` file is.

#. Start Mopidy, find the music library in a client, and play some local music!
