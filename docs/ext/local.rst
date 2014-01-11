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

.. literalinclude:: ../../mopidy/local/ext.conf
    :language: ini


Configuration values
====================

.. confval:: local/enabled

    If the local extension should be enabled or not.

.. confval:: local/library

    Local library provider to use, change this if you want to use a third party
    library for local files.

.. confval:: local/media_dir

    Path to directory with local media files.

.. confval:: local/data_dir

    Path to directory to store local metadata such as libraries and playlists
    in.

.. confval:: local/playlists_dir

    Path to playlists directory with m3u files for local media.

.. confval:: local/scan_timeout

    Number of milliseconds before giving up scanning a file and moving on to
    the next file.

.. confval:: local/scan_flush_threshold

    Number of tracks to wait before telling library it should try and store
    its progress so far. Some libraries might not respect this setting.

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
disable the current default library ``json``, replacing it with a third
party one. When running :command:`mopidy local scan` mopidy will populate
whatever the current active library is with data. Only one library may be
active at a time.

To create a new library provider you must create class that implements the
:class:`~mopidy.local.Library` interface and install it in the extension
registry under ``local:library``. Any data that the library needs to store on
disc should be stored in :confval:`local/data_dir` using the library name as
part of the filename or directory to avoid any conflicts.
