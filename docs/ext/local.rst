.. _ext-local:

************
Mopidy-Local
************

Extension for playing music from a local music archive.

This backend handles URIs starting with ``local:``.


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

.. confval:: local/scan_timeout

    Number of milliseconds before giving up scanning a file and moving on to
    the next file.

.. confval:: local/excluded_file_extensions

    File extensions to exclude when scanning the media directory. Values
    should be separated by either comma or newline.


Usage
=====

If you want use Mopidy to play music you have locally at your machine, you need
to review and maybe change some of the local extension config values. See above
for a complete list. Then you need to generate a local library for your local
music...


.. _generating-a-local-library:

Generating a local library
--------------------------

The command :command:`mopidy local scan` will scan the path set in the
:confval:`local/media_dir` config value for any audio files and build a
library.

To make a local library for your music available for Mopidy:

#. Ensure that the :confval:`local/media_dir` config value points to where your
   music is located. Check the current setting by running::

    mopidy config

#. Scan your media library.::

    mopidy local scan

#. Start Mopidy, find the music library in a client, and play some local music!


Pluggable library support
-------------------------

Local libraries are fully pluggable. What this means is that users may opt to
disable the current default library ``local-json``, replacing it with a third
party one. When running :command:`mopidy local scan` mopidy will populate
whatever the current active library is with data. Only one library may be
active at a time.


*****************
Mopidy-Local-JSON
*****************

Extension for storing local music library in a JSON file, default built in
library for local files.


Default configuration
=====================

.. literalinclude:: ../../mopidy/backends/local/json/ext.conf
    :language: ini


Configuration values
====================

.. confval:: local-json/enabled

    If the local-json extension should be enabled or not.

.. confval:: local-json/json_file

    Path to a file to store the gzipped JSON data in.
