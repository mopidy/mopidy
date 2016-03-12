.. _ext-m3u:

**********
Mopidy-M3U
**********

Mopidy-M3U is an extension for reading and writing M3U playlists stored
on disk. It is bundled with Mopidy and enabled by default.

This backend handles URIs starting with ``m3u:``.


.. _m3u-migration:

Migrating from Mopidy-Local playlists
=====================================

Mopidy-M3U was split out of the Mopidy-Local extension in Mopidy 1.0. To
migrate your playlists from Mopidy-Local, simply move them from the
:confval:`local/playlists_dir` directory to the :confval:`m3u/playlists_dir`
directory. Assuming you have not changed the default config, run the following
commands to migrate::

    mkdir -p ~/.local/share/mopidy/m3u/
    mv ~/.local/share/mopidy/local/playlists/* ~/.local/share/mopidy/m3u/


Editing playlists
=================

There is a core playlist API in place for editing playlists. This is supported
by a few Mopidy clients, but not through Mopidy's MPD server yet.

It is possible to edit playlists by editing the M3U files located in the
:confval:`m3u/playlists_dir` directory, usually
:file:`~/.local/share/mopidy/m3u/`, by hand with a text editor. See `Wikipedia
<https://en.wikipedia.org/wiki/M3U>`__ for a short description of the quite
simple M3U playlist format.


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/m3u/ext.conf
    :language: ini

.. confval:: m3u/enabled

    If the M3U extension should be enabled or not.

.. confval:: m3u/playlists_dir

    Path to directory with M3U files. Unset by default, in which case the
    extension's data dir is used to store playlists.

.. confval:: m3u/base_dir

    Path to base directory for resolving relative paths in M3U files.
    If not set, relative paths are resolved based on the M3U file's
    location.

.. confval:: m3u/default_encoding

    Text encoding used for files with extension ``.m3u``.  Default is
    ``latin-1``. Note that files with extension ``.m3u8`` are always
    expected to be UTF-8 encoded.

.. confval:: m3u/default_extension

    The file extension for M3U playlists created using the core playlist
    API. Default is ``.m3u8``.
