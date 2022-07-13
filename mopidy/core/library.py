import collections
import contextlib
import logging
import operator
import urllib
from collections.abc import Mapping

from mopidy import exceptions, models
from mopidy.internal import deprecation, validation

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _backend_error_handling(backend, reraise=None):
    try:
        yield
    except exceptions.ValidationError as e:
        logger.error(
            "%s backend returned bad data: %s",
            backend.actor_ref.actor_class.__name__,
            e,
        )
    except Exception as e:
        if reraise and isinstance(e, reraise):
            raise
        logger.exception(
            "%s backend caused an exception.",
            backend.actor_ref.actor_class.__name__,
        )


class LibraryController:
    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def _get_backend(self, uri):
        uri_scheme = urllib.parse.urlparse(uri).scheme
        return self.backends.with_library.get(uri_scheme, None)

    def _get_backends_to_uris(self, uris):
        if uris:
            backends_to_uris = collections.defaultdict(list)
            for uri in uris:
                backend = self._get_backend(uri)
                if backend is not None:
                    backends_to_uris[backend].append(uri)
        else:
            backends_to_uris = {
                b: None for b in self.backends.with_library.values()
            }
        return backends_to_uris

    def browse(self, uri):
        """
        Browse directories and tracks at the given ``uri``.

        ``uri`` is a string which represents some directory belonging to a
        backend. To get the intial root directories for backends pass
        :class:`None` as the URI.

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

        .. versionadded:: 0.18
        """
        if uri is None:
            return self._roots()
        elif not uri.strip():
            return []
        validation.check_uri(uri)
        return self._browse(uri)

    def _roots(self):
        directories = set()
        backends = self.backends.with_library_browse.values()
        futures = {b: b.library.root_directory for b in backends}
        for backend, future in futures.items():
            with _backend_error_handling(backend):
                root = future.get()
                validation.check_instance(root, models.Ref)
                directories.add(root)
        return sorted(directories, key=operator.attrgetter("name"))

    def _browse(self, uri):
        scheme = urllib.parse.urlparse(uri).scheme
        backend = self.backends.with_library_browse.get(scheme)

        if not backend:
            return []

        with _backend_error_handling(backend):
            result = backend.library.browse(uri).get()
            validation.check_instances(result, models.Ref)
            return result

        return []

    def get_distinct(self, field, query=None):
        """
        List distinct values for a given field from the library.

        This has mainly been added to support the list commands the MPD
        protocol supports in a more sane fashion. Other frontends are not
        recommended to use this method.

        :param string field: Any one of ``uri``, ``track_name``, ``album``,
            ``artist``, ``albumartist``, ``composer``, ``performer``,
            ``track_no``, ``genre``, ``date``, ``comment``, ``disc_no``,
            ``musicbrainz_albumid``, ``musicbrainz_artistid``, or
            ``musicbrainz_trackid``.
        :param dict query: Query to use for limiting results, see
            :meth:`search` for details about the query format.
        :rtype: set of values corresponding to the requested field type.

        .. versionadded:: 1.0
        """
        if field == "track":
            deprecation.warn(
                f"core.library.get_distinct:field_arg:{field}",
                pending=False,
            )
            field_type = str
        else:
            validation.check_choice(field, validation.DISTINCT_FIELDS.keys())
            field_type = validation.DISTINCT_FIELDS.get(field)
        query is None or validation.check_query(query)  # TODO: normalize?

        compat_field = {"track_name": "track"}.get(field, field)

        result = set()
        futures = {
            b: b.library.get_distinct(compat_field, query)
            for b in self.backends.with_library.values()
        }
        for backend, future in futures.items():
            with _backend_error_handling(backend):
                values = future.get()
                if values is not None:
                    validation.check_instances(values, field_type)
                    result.update(values)
        return result

    def get_images(self, uris):
        """Lookup the images for the given URIs

        Backends can use this to return image URIs for any URI they know about
        be it tracks, albums, playlists. The lookup result is a dictionary
        mapping the provided URIs to lists of images.

        Unknown URIs or URIs the corresponding backend couldn't find anything
        for will simply return an empty list for that URI.

        :param uris: list of URIs to find images for
        :type uris: list of string
        :rtype: {uri: tuple of :class:`mopidy.models.Image`}

        .. versionadded:: 1.0
        """
        validation.check_uris(uris)

        futures = {
            backend: backend.library.get_images(backend_uris)
            for (backend, backend_uris) in self._get_backends_to_uris(
                uris
            ).items()
            if backend_uris
        }

        results = {uri: () for uri in uris}
        for backend, future in futures.items():
            with _backend_error_handling(backend):
                if future.get() is None:
                    continue
                validation.check_instance(future.get(), Mapping)
                for uri, images in future.get().items():
                    if uri not in uris:
                        raise exceptions.ValidationError(
                            f"Got unknown image URI: {uri}"
                        )
                    validation.check_instances(images, models.Image)
                    results[uri] += tuple(images)
        return results

    def lookup(self, uris):
        """
        Lookup the given URIs.

        If the URI expands to multiple tracks, the returned list will contain
        them all.

        :param uris: track URIs
        :type uris: list of string
        :rtype: {uri: list of :class:`mopidy.models.Track`}
        """
        validation.check_uris(uris)

        futures = {}
        results = {u: [] for u in uris}

        # TODO: lookup(uris) to backend APIs
        for backend, backend_uris in self._get_backends_to_uris(uris).items():
            if backend_uris:
                for u in backend_uris:
                    futures[(backend, u)] = backend.library.lookup(u)

        for (backend, u), future in futures.items():
            with _backend_error_handling(backend):
                result = future.get()
                if result is not None:
                    validation.check_instances(result, models.Track)
                    # TODO Consider making Track.uri field mandatory, and
                    # then remove this filtering of tracks without URIs.
                    results[u] = [r for r in result if r.uri]

        return results

    def refresh(self, uri=None):
        """
        Refresh library. Limit to URI and below if an URI is given.

        :param uri: directory or track URI
        :type uri: string
        """
        uri is None or validation.check_uri(uri)

        futures = {}
        backends = {}
        uri_scheme = urllib.parse.urlparse(uri).scheme if uri else None

        for backend_scheme, backend in self.backends.with_library.items():
            backends.setdefault(backend, set()).add(backend_scheme)

        for backend, backend_schemes in backends.items():
            if uri_scheme is None or uri_scheme in backend_schemes:
                futures[backend] = backend.library.refresh(uri)

        for backend, future in futures.items():
            with _backend_error_handling(backend):
                future.get()

    def search(self, query, uris=None, exact=False):
        """
        Search the library for tracks where ``field`` contains ``values``.

        ``field`` can be one of ``uri``, ``track_name``, ``album``, ``artist``,
        ``albumartist``, ``composer``, ``performer``, ``track_no``, ``genre``,
        ``date``, ``comment``, ``disc_no``, ``musicbrainz_albumid``,
        ``musicbrainz_artistid``, ``musicbrainz_trackid`` or ``any``.

        If ``uris`` is given, the search is limited to results from within the
        URI roots. For example passing ``uris=['file:']`` will limit the search
        to the local backend.

        Examples::

            # Returns results matching 'a' in any backend
            search({'any': ['a']})

            # Returns results matching artist 'xyz' in any backend
            search({'artist': ['xyz']})

            # Returns results matching 'a' and 'b' and artist 'xyz' in any
            # backend
            search({'any': ['a', 'b'], 'artist': ['xyz']})

            # Returns results matching 'a' if within the given URI roots
            # "file:///media/music" and "spotify:"
            search({'any': ['a']}, uris=['file:///media/music', 'spotify:'])

            # Returns results matching artist 'xyz' and 'abc' in any backend
            search({'artist': ['xyz', 'abc']})

        :param query: one or more queries to search for
        :type query: dict
        :param uris: zero or more URI roots to limit the search to
        :type uris: list of string or :class:`None`
        :param exact: if the search should use exact matching
        :type exact: :class:`bool`
        :rtype: list of :class:`mopidy.models.SearchResult`

        .. versionadded:: 1.0
            The ``exact`` keyword argument.
        """
        query = _normalize_query(query)

        uris is None or validation.check_uris(uris)
        validation.check_query(query)
        validation.check_boolean(exact)

        if not query:
            return []

        futures = {}
        for backend, backend_uris in self._get_backends_to_uris(uris).items():
            futures[backend] = backend.library.search(
                query=query, uris=backend_uris, exact=exact
            )

        # Some of our tests check for LookupError to catch bad queries. This is
        # silly and should be replaced with query validation before passing it
        # to the backends.
        reraise = (TypeError, LookupError)

        results = []
        for backend, future in futures.items():
            try:
                with _backend_error_handling(backend, reraise=reraise):
                    result = future.get()
                    if result is not None:
                        validation.check_instance(result, models.SearchResult)
                        results.append(result)
            except TypeError:
                backend_name = backend.actor_ref.actor_class.__name__
                logger.warning(
                    '%s does not implement library.search() with "exact" '
                    "support. Please upgrade it.",
                    backend_name,
                )

        return results


def _normalize_query(query):
    broken_client = False
    # TODO: this breaks if query is not a dictionary like object...
    for (field, values) in query.items():
        if isinstance(values, str):
            broken_client = True
            query[field] = [values]
    if broken_client:
        logger.warning(
            "A client or frontend made a broken library search. Values in "
            "queries must be lists of strings, not a string. Please check what"
            " sent this query and file a bug. Query: %s",
            query,
        )
    if not query:
        logger.warning(
            "A client or frontend made a library search with an empty query. "
            "This is strongly discouraged. Please check what sent this query "
            "and file a bug."
        )
    return query
