.. _ext-local:

************
Mopidy-Local
************

Mopidy-Local is an extension for playing music from your local music archive.
It is bundled with Mopidy and enabled by default. Though, you'll have to scan
your music collection to build a cache of metadata before the Mopidy-Local
will be able to play your music.

This backend handles URIs starting with ``local:``.


.. _generating-a-local-library:

Generating a local library
==========================

The command :command:`mopidy local scan` will scan the path set in the
:confval:`local/media_dir` config value for any audio files and build a
library of metadata.

To make a local library for your music available for Mopidy:

#. Ensure that the :confval:`local/media_dir` config value points to where your
   music is located. Check the current setting by running::

    mopidy config

#. Scan your media library.::

    mopidy local scan

#. Start Mopidy, find the music library in a client, and play some local music!


Updating the local library
==========================

When you've added or removed music in your collection and want to update
Mopidy's index of your local library, you need to rescan::

    mopidy local scan

Note that if you are using the default local library storage, ``json``, you
need to restart Mopidy after the scan completes for the updated index to be
used.

If you want index updates to come into effect immediately, you can try out
`Mopidy-Local-SQLite <https://github.com/mopidy/mopidy-local-sqlite>`_, which
will probably become the default backend in the near future.


Pluggable library support
=========================

Local libraries are fully pluggable. What this means is that users may opt to
disable the current default library ``json``, replacing it with a third
party one. When running :command:`mopidy local scan` Mopidy will populate
whatever the current active library is with data. Only one library may be
active at a time.

To create a new library provider you must create class that implements the
:class:`mopidy.local.Library` interface and install it in the extension
registry under ``local:library``. Any data that the library needs to store on
disc should be stored in the extension's data dir, as returned by
:meth:`~mopidy.ext.Extension.get_data_dir`.


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/local/ext.conf
    :language: ini

.. confval:: local/enabled

    If the local extension should be enabled or not.

.. confval:: local/library

    Local library provider to use, change this if you want to use a third party
    library for local files.

.. confval:: local/media_dir

    Path to directory with local media files.

.. confval:: local/scan_timeout

    Number of milliseconds before giving up scanning a file and moving on to
    the next file.

.. confval:: local/scan_follow_symlinks

    If we should follow symlinks found in :confval:`local/media_dir`

.. confval:: local/scan_flush_threshold

    Number of tracks to wait before telling library it should try and store
    its progress so far. Some libraries might not respect this setting.
    Set this to zero to disable flushing.

.. confval:: local/excluded_file_extensions

    File extensions to exclude when scanning the media directory. Values
    should be separated by either comma or newline.
