from __future__ import absolute_import, unicode_literals

import collections
import operator
import urlparse

import pykka


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

    def browse(self, uri):
        """
        Browse directories and tracks at the given ``uri``.

        ``uri`` is a string which represents some directory belonging to a
        backend. To get the intial root directories for backends pass None as
        the URI.

        Returns a list of :class:`mopidy.models.Ref` objects for the
        directories and tracks at the given ``uri``.

        The :class:`~mopidy.models.Ref` objects representing tracks keep the
        track's original URI. A matching pair of objects can look like this::

            Track(uri='dummy:/foo.mp3', name='foo', artists=..., album=...)
            Ref.track(uri='dummy:/foo.mp3', name='foo')

        The :class:`~mopidy.models.Ref` objects representing directories have
        backend specific URIs. These are opaque values, so no one but the
        backend that created them should try and derive any meaning from them.
        The only valid exception to this is checking the scheme, as it is used
        to route browse requests to the correct backend.

        For example, the dummy library's ``/bar`` directory could be returned
        like this::

            Ref.directory(uri='dummy:directory:/bar', name='bar')

        :param string uri: URI to browse
        :rtype: list of :class:`mopidy.models.Ref`
        """
        if uri is None:
            backends = self.backends.with_library_browse.values()
            unique_dirs = {b.library.root_directory.get() for b in backends}
            return sorted(unique_dirs, key=operator.attrgetter('name'))

        scheme = urlparse.urlparse(uri).scheme
        backend = self.backends.with_library_browse.get(scheme)
        if not backend:
            return []
        return backend.library.browse(uri).get()

    def get_distinct(self, field, query=None):
        """
        List distinct values for a given field from the library.

        This has mainly been added to support the list commands the MPD
        protocol supports in a more sane fashion. Other frontends are not
        recommended to use this method.

        :param string field: One of ``artist``, ``albumartist``, ``album``,
            ``composer``, ``performer``, ``date``or ``genre``.
        :param dict query: Query to use for limiting results, see
            :meth:`search` for details about the query format.
        :rtype: set of values corresponding to the requested field type.
        """
        futures = [b.library.get_distinct(field, query)
                   for b in self.backends.with_library.values()]
        result = set()
        for r in pykka.get_all(futures):
            result.update(r)
        return result

    def get_images(self, uris):
        """Lookup the images for the given URIs

        Backends can use this to return image URIs for any URI they know about
        be it tracks, albums, playlists... The lookup result is a dictionary
        mapping the provided URIs to lists of images.

        Unknown URIs or URIs the corresponding backend couldn't find anything
        for will simply return an empty list for that URI.

        :param list uris: list of URIs to find images for
        :rtype: {uri: tuple of :class:`mopidy.models.Image`}
        """
        futures = [
            backend.library.get_images(backend_uris)
            for (backend, backend_uris)
            in self._get_backends_to_uris(uris).items() if backend_uris]

        results = {uri: tuple() for uri in uris}
        for r in pykka.get_all(futures):
            for uri, images in r.items():
                results[uri] += tuple(images)
        return results

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

    def lookup(self, uri=None, uris=None):
        """
        Lookup the given URI.

        If the URI expands to multiple tracks, the returned list will contain
        them all.

        :param uri: track URI
        :type uri: string or :class:`None`
        :param uris: track URIs
        :type uris: list of string or :class:`None`
        :rtype: list of :class:`mopidy.models.Track` if uri was set or a
            ``{uri: list of tracks}`` if uris was set.
        """
        none_set = uri is None and uris is None
        both_set = uri is not None and uris is not None

        if none_set or both_set:
            raise ValueError("One of 'uri' or 'uris' must be set")

        futures = {}
        result = {}
        backends = self._get_backends_to_uris([uri] if uri else uris)

        # TODO: lookup(uris) to backend APIs
        for backend, backend_uris in backends.items():
            for u in backend_uris or []:
                futures[u] = backend.library.lookup(u)

        for u, future in futures.items():
            result[u] = future.get()

        if uri:
            return result.get(uri, [])
        return result

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
