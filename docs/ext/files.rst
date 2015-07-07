.. _ext-files:

************
Mopidy-Files
************

Mopidy-Files is an extension for playing music from your local music archive.
It is bundled with Mopidy and enabled by default. 
It allows you to browse through your local file system.
Only files that are considered playable will be shown.

This backend handles URIs starting with ``file:``.


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/files/ext.conf
    :language: ini

.. confval:: files/enabled

    If the files extension should be enabled or not.

.. confval:: files/media_dirs

    A list of directories to be browsable.
    Optionally the path can be followed by ``|`` and a name that will be shown for that path.

.. confval:: files/show_dotfiles

    Whether to show hidden files and directories that start with a dot.
    Default is false.

.. confval:: files/follow_symlinks

    Whether to follow symbolic links found in :confval:`files/media_dir`.
    Directories and files that are outside the configured directories will not be shown.
    Default is false.

.. confval:: files/metadata_timeout

    Number of milliseconds before giving up scanning a file and moving on to
    the next file. Reducing the value might speed up the directory listing,
    but can lead to some tracks not being shown.
