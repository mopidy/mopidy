.. _ext-file:

************
Mopidy-File
************

Mopidy-File is an extension for playing music from your local music archive.
It is bundled with Mopidy and enabled by default. 
It allows you to browse through your local file system.
Only files that are considered playable will be shown.

This backend handles URIs starting with ``file:``.


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/file/ext.conf
    :language: ini

.. confval:: file/enabled

    If the file extension should be enabled or not.

.. confval:: file/media_dirs

    A list of directories to be browsable.
    Optionally the path can be followed by ``|`` and a name that will be shown
    for that path.

.. confval:: file/show_dotfiles

    Whether to show hidden files and directories that start with a dot.
    Default is false.

.. confval:: file/excluded_file_extensions

    File extensions to exclude when scanning the media directory. Values
    should be separated by either comma or newline.

.. confval:: file/follow_symlinks

    Whether to follow symbolic links found in :confval:`file/media_dirs`.
    Directories and files that are outside the configured directories will not
    be shown. Default is false.

.. confval:: file/metadata_timeout

    Number of milliseconds before giving up scanning a file and moving on to
    the next file. Reducing the value might speed up the directory listing,
    but can lead to some tracks not being shown.
