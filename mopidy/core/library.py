from __future__ import unicode_literals

import collections
import re
import urlparse

import pykka

from mopidy.models import Ref


class LibraryController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def _get_backend(self, uri):
        uri_scheme = urlparse.urlparse(uri).scheme
        return self.backends.with_library.get(uri_scheme, None)

    def _get_backends_to_uris(self, uris):
        if uris:
            backends_to_uris = collections.defaultdict(list)
            for uri in uris:
                backend = self._get_backend(uri)
                if backend is not None:
                    backends_to_uris[backend].append(uri)
        else:
            backends_to_uris = dict([
                (b, None) for b in self.backends.with_library.values()])
        return backends_to_uris

    def browse(self, path):
        """
        Browse directories and tracks at the given ``path``.

        ``path`` is a string that always starts with "/". It points to a
        directory in Mopidy's virtual file system.

        Returns a list of :class:`mopidy.models.Ref` objects for the
        directories and tracks at the given ``path``.

        The :class:`~mopidy.models.Ref` objects representing tracks keep the
        track's original URI. A matching pair of objects can look like this::

            Track(uri='dummy:/foo.mp3', name='foo', artists=..., album=...)
            Ref.track(uri='dummy:/foo.mp3', name='foo')

        The :class:`~mopidy.models.Ref` objects representing directories have
        plain paths, not including any URI schema. For example, the dummy
        library's ``/bar`` directory is returned like this::

            Ref.directory(uri='/dummy/bar', name='bar')

        Note to backend implementors: The ``/dummy`` part of the URI is added
        by Mopidy core, not the individual backends.

        :param path: path to browse
        :type path: string
        :rtype: list of :class:`mopidy.models.Ref`
        """
        if not path.startswith('/'):
            return []

        if path == '/':
            return [
                Ref.directory(uri='/%s' % name, name=name)
                for name in self.backends.with_browsable_library.keys()]

        groups = re.match('/(?P<library>[^/]+)(?P<path>.*)', path).groupdict()
        library_name = groups['library']
        backend_path = groups['path']
        if not backend_path.startswith('/'):
            backend_path = '/%s' % backend_path

        backend = self.backends.with_browsable_library.get(library_name, None)
        if not backend:
            return []

        refs = backend.library.browse(backend_path).get()
        result = []
        for ref in refs:
            if ref.type == Ref.DIRECTORY:
                uri = '/'.join(['', library_name, ref.uri.lstrip('/')])
                result.append(ref.copy(uri=uri))
            else:
                result.append(ref)
        return result

    def find_exact(self, query=None, uris=None, **kwargs):
        """
        Search the library for tracks where ``field`` is ``values``.

        If the query is empty, and the backend can support it, all available
        tracks are returned.

        If ``uris`` is given, the search is limited to results from within the
        URI roots. For example passing ``uris=['file:']`` will limit the search
        to the local backend.

        Examples::

            # Returns results matching 'a' from any backend
            find_exact({'any': ['a']})
            find_exact(any=['a'])

            # Returns results matching artist 'xyz' from any backend
            find_exact({'artist': ['xyz']})
            find_exact(artist=['xyz'])

            # Returns results matching 'a' and 'b' and artist 'xyz' from any
            # backend
            find_exact({'any': ['a', 'b'], 'artist': ['xyz']})
            find_exact(any=['a', 'b'], artist=['xyz'])

            # Returns results matching 'a' if within the given URI roots
            # "file:///media/music" and "spotify:"
            find_exact(
                {'any': ['a']}, uris=['file:///media/music', 'spotify:'])
            find_exact(any=['a'], uris=['file:///media/music', 'spotify:'])

        :param query: one or more queries to search for
        :type query: dict
        :param uris: zero or more URI roots to limit the search to
        :type uris: list of strings or :class:`None`
        :rtype: list of :class:`mopidy.models.SearchResult`
        """
        query = query or kwargs
        futures = [
            backend.library.find_exact(query=query, uris=backend_uris)
            for (backend, backend_uris)
            in self._get_backends_to_uris(uris).items()]
        return [result for result in pykka.get_all(futures) if result]

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
            futures = [b.library.refresh(uri)
                       for b in self.backends.with_library.values()]
            pykka.get_all(futures)

    def search(self, query=None, uris=None, **kwargs):
        """
        Search the library for tracks where ``field`` contains ``values``.

        If the query is empty, and the backend can support it, all available
        tracks are returned.

        If ``uris`` is given, the search is limited to results from within the
        URI roots. For example passing ``uris=['file:']`` will limit the search
        to the local backend.

        Examples::

            # Returns results matching 'a' in any backend
            search({'any': ['a']})
            search(any=['a'])

            # Returns results matching artist 'xyz' in any backend
            search({'artist': ['xyz']})
            search(artist=['xyz'])

            # Returns results matching 'a' and 'b' and artist 'xyz' in any
            # backend
            search({'any': ['a', 'b'], 'artist': ['xyz']})
            search(any=['a', 'b'], artist=['xyz'])

            # Returns results matching 'a' if within the given URI roots
            # "file:///media/music" and "spotify:"
            search({'any': ['a']}, uris=['file:///media/music', 'spotify:'])
            search(any=['a'], uris=['file:///media/music', 'spotify:'])

        :param query: one or more queries to search for
        :type query: dict
        :param uris: zero or more URI roots to limit the search to
        :type uris: list of strings or :class:`None`
        :rtype: list of :class:`mopidy.models.SearchResult`
        """
        query = query or kwargs
        futures = [
            backend.library.search(query=query, uris=backend_uris)
            for (backend, backend_uris)
            in self._get_backends_to_uris(uris).items()]
        return [result for result in pykka.get_all(futures) if result]
