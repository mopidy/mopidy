import itertools
import urlparse

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

    def delete(self, uri):
        """
        Delete playlist identified by the URI.

        If the URI doesn't match the URI schemes handled by the current
        backends, nothing happens.

        :param uri: URI of the playlist to delete
        :type uri: string
        """
        uri_scheme = urlparse.urlparse(uri).scheme
        backend = self.backends.by_uri_scheme.get(uri_scheme, None)
        if backend:
            return backend.stored_playlists.delete(uri).get()

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
        in any other playlist sources. Returns :class:`None` if not found.

        :param uri: playlist URI
        :type uri: string
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        uri_scheme = urlparse.urlparse(uri).scheme
        backend = self.backends.by_uri_scheme.get(uri_scheme, None)
        if backend:
            return backend.stored_playlists.lookup(uri).get()
        else:
            return None

    def refresh(self, uri_scheme=None):
        """
        Refresh the stored playlists in :attr:`playlists`.

        If ``uri_scheme`` is :class:`None`, all backends are asked to refresh.
        If ``uri_scheme`` is an URI scheme handled by a backend, only that
        backend is asked to refresh. If ``uri_scheme`` doesn't match any
        current backend, nothing happens.

        :param uri_scheme: limit to the backend matching the URI scheme
        :type uri_scheme: string
        """
        if uri_scheme is None:
            futures = [b.stored_playlists.refresh() for b in self.backends]
            pykka.get_all(futures)
        else:
            if uri_scheme in self.backends.by_uri_scheme:
                backend = self.backends.by_uri_scheme[uri_scheme]
                backend.stored_playlists.refresh().get()

    def save(self, playlist):
        """
        Save the playlist to the set of stored playlists.

        Returns the saved playlist. The return playlist may differ from the
        saved playlist. E.g. if the playlist name was changed, the returned
        playlist may have a different URI. The caller of this method should
        throw away the playlist sent to this method, and use the returned
        playlist instead.

        :param playlist: the playlist
        :type playlist: :class:`mopidy.models.Playlist`
        :rtype: :class:`mopidy.models.Playlist`
        """
        # TODO Support multiple backends
        return self.backends[0].stored_playlists.save(playlist).get()
