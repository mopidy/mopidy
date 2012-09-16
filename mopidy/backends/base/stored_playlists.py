from copy import copy


class BaseStoredPlaylistsProvider(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend
        self._playlists = []

    @property
    def playlists(self):
        """
        Currently stored playlists.

        Read/write. List of :class:`mopidy.models.Playlist`.
        """
        return copy(self._playlists)

    @playlists.setter
    def playlists(self, playlists):
        self._playlists = playlists

    def create(self, name):
        """
        See :meth:`mopidy.backends.base.StoredPlaylistsController.create`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def delete(self, playlist):
        """
        See :meth:`mopidy.backends.base.StoredPlaylistsController.delete`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def lookup(self, uri):
        """
        See :meth:`mopidy.backends.base.StoredPlaylistsController.lookup`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def refresh(self):
        """
        See :meth:`mopidy.backends.base.StoredPlaylistsController.refresh`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def rename(self, playlist, new_name):
        """
        See :meth:`mopidy.backends.base.StoredPlaylistsController.rename`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def save(self, playlist):
        """
        See :meth:`mopidy.backends.base.StoredPlaylistsController.save`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError
