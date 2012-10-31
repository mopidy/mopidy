import itertools

import pykka


class StoredPlaylistsController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    @property
    def playlists(self):
        """
        Currently stored playlists.

        Read-only. List of :class:`mopidy.models.Playlist`.
        """
        futures = [b.stored_playlists.playlists for b in self.backends]
        results = pykka.get_all(futures)
        return list(itertools.chain(*results))

    def create(self, name, uri_scheme=None):
        """
        Create a new playlist.

        If ``uri_scheme`` matches an URI scheme handled by a current backend,
        that backend is asked to create the playlist. If ``uri_scheme`` is
        :class:`None` or doesn't match a current backend, the first backend is
        asked to create the playlist.

        :param name: name of the new playlist
        :type name: string
        :param uri_scheme: use the backend matching the URI scheme
        :type uri_scheme: string
        :rtype: :class:`mopidy.models.Playlist`
        """
        if uri_scheme in self.backends.by_uri_scheme:
            backend = self.backends.by_uri_scheme[uri_scheme]
        else:
            backend = self.backends[0]
        return backend.stored_playlists.create(name).get()

    def delete(self, playlist):
        """
        Delete playlist.

        :param playlist: the playlist to delete
        :type playlist: :class:`mopidy.models.Playlist`
        """
        # TODO Support multiple backends
        return self.backends[0].stored_playlists.delete(playlist).get()

    def get(self, **criteria):
        """
        Get playlist by given criterias from the set of stored playlists.

        Raises :exc:`LookupError` if a unique match is not found.

        Examples::

            get(name='a')            # Returns track with name 'a'
            get(uri='xyz')           # Returns track with URI 'xyz'
            get(name='a', uri='xyz') # Returns track with name 'a' and URI
                                     # 'xyz'

        :param criteria: one or more criteria to match by
        :type criteria: dict
        :rtype: :class:`mopidy.models.Playlist`
        """
        matches = self.playlists
        for (key, value) in criteria.iteritems():
            matches = filter(lambda p: getattr(p, key) == value, matches)
        if len(matches) == 1:
            return matches[0]
        criteria_string = ', '.join(
            ['%s=%s' % (k, v) for (k, v) in criteria.iteritems()])
        if len(matches) == 0:
            raise LookupError('"%s" match no playlists' % criteria_string)
        else:
            raise LookupError(
                '"%s" match multiple playlists' % criteria_string)

    def lookup(self, uri):
        """
        Lookup playlist with given URI in both the set of stored playlists and
        in any other playlist sources.

        :param uri: playlist URI
        :type uri: string
        :rtype: :class:`mopidy.models.Playlist`
        """
        # TODO Support multiple backends
        return self.backends[0].stored_playlists.lookup(uri).get()

    def refresh(self):
        """
        Refresh the stored playlists in :attr:`playlists`.
        """
        # TODO Support multiple backends
        return self.backends[0].stored_playlists.refresh().get()

    def rename(self, playlist, new_name):
        """
        Rename playlist.

        :param playlist: the playlist
        :type playlist: :class:`mopidy.models.Playlist`
        :param new_name: the new name
        :type new_name: string
        """
        # TODO Support multiple backends
        return self.backends[0].stored_playlists.rename(
            playlist, new_name).get()

    def save(self, playlist):
        """
        Save the playlist to the set of stored playlists.

        :param playlist: the playlist
        :type playlist: :class:`mopidy.models.Playlist`
        """
        # TODO Support multiple backends
        return self.backends[0].stored_playlists.save(playlist).get()
