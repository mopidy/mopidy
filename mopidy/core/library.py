from __future__ import unicode_literals

import urlparse

import pykka


class LibraryController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def _get_backend(self, uri):
        uri_scheme = urlparse.urlparse(uri).scheme
        return self.backends.with_library_by_uri_scheme.get(uri_scheme, None)

    def find_exact(self, query=None, **kwargs):
        """
        Search the library for tracks where ``field`` is ``values``.

        Examples::

            # Returns results matching 'a'
            find_exact({'any': ['a']})
            find_exact(any=['a'])

            # Returns results matching artist 'xyz'
            find_exact({'artist': ['xyz']})
            find_exact(artist=['xyz'])

            # Returns results matching 'a' and 'b' and artist 'xyz'
            find_exact({'any': ['a', 'b'], 'artist': ['xyz']})
            find_exact(any=['a', 'b'], artist=['xyz'])

        :param query: one or more queries to search for
        :type query: dict
        :rtype: list of :class:`mopidy.models.SearchResult`
        """
        query = query or kwargs
        futures = [
            b.library.find_exact(**query) for b in self.backends.with_library]
        return pykka.get_all(futures)

    def lookup(self, uri):
        """
        Lookup the given URI.

        If the URI expands to multiple tracks, the returned list will contain
        them all.

        :param uri: track URI
        :type uri: string
        :rtype: list of :class:`mopidy.models.Track`
        """
        backend = self._get_backend(uri)
        if backend:
            return backend.library.lookup(uri).get()
        else:
            return []

    def refresh(self, uri=None):
        """
        Refresh library. Limit to URI and below if an URI is given.

        :param uri: directory or track URI
        :type uri: string
        """
        if uri is not None:
            backend = self._get_backend(uri)
            if backend:
                backend.library.refresh(uri).get()
        else:
            futures = [
                b.library.refresh(uri) for b in self.backends.with_library]
            pykka.get_all(futures)

    def search(self, query=None, **kwargs):
        """
        Search the library for tracks where ``field`` contains ``values``.

        Examples::

            # Returns results matching 'a'
            search({'any': ['a']})
            search(any=['a'])

            # Returns results matching artist 'xyz'
            search({'artist': ['xyz']})
            search(artist=['xyz'])

            # Returns results matching 'a' and 'b' and artist 'xyz'
            search({'any': ['a', 'b'], 'artist': ['xyz']})
            search(any=['a', 'b'], artist=['xyz'])

        :param query: one or more queries to search for
        :type query: dict
        :rtype: list of :class:`mopidy.models.SearchResult`
        """
        query = query or kwargs
        futures = [
            b.library.search(**query) for b in self.backends.with_library]
        return pykka.get_all(futures)
