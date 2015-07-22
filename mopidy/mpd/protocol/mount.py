from __future__ import absolute_import, unicode_literals

from mopidy.mpd import exceptions, protocol


@protocol.commands.add('mount')
def mount(context, path, uri):
    """
    *musicpd.org, mounts and neighbors section:*

        ``mount {PATH} {URI}``

        Mount the specified remote storage URI at the given path. Example::

            mount foo nfs://192.168.1.4/export/mp3

    .. versionadded:: 0.19
        New in MPD protocol version 0.19
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('unmount')
def unmount(context, path):
    """
    *musicpd.org, mounts and neighbors section:*

        ``unmount {PATH}``

        Unmounts the specified path. Example::

            unmount foo

    .. versionadded:: 0.19
        New in MPD protocol version 0.19
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('listmounts')
def listmounts(context):
    """
    *musicpd.org, mounts and neighbors section:*

        ``listmounts``

        Queries a list of all mounts. By default, this contains just the
        configured music_directory. Example::

            listmounts
            mount:
            storage: /home/foo/music
            mount: foo
            storage: nfs://192.168.1.4/export/mp3
            OK

    .. versionadded:: 0.19
        New in MPD protocol version 0.19
    """
    raise exceptions.MpdNotImplemented  # TODO


@protocol.commands.add('listneighbors')
def listneighbors(context):
    """
    *musicpd.org, mounts and neighbors section:*

        ``listneighbors``

        Queries a list of "neighbors" (e.g. accessible file servers on the
        local net). Items on that list may be used with the mount command.
        Example::

            listneighbors
            neighbor: smb://FOO
            name: FOO (Samba 4.1.11-Debian)
            OK

    .. versionadded:: 0.19
        New in MPD protocol version 0.19
    """
    raise exceptions.MpdNotImplemented  # TODO
