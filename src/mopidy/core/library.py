from __future__ import annotations

import collections
import contextlib
import logging
import operator
import urllib.parse
from collections.abc import Generator, Iterable, Mapping
from typing import TYPE_CHECKING, Any, cast

from pykka.typing import proxy_method

from mopidy import exceptions
from mopidy.internal import deprecation, validation
from mopidy.models import Image, Ref, SearchResult, Track
from mopidy.types import DistinctField, Query, SearchField, Uri, UriScheme

if TYPE_CHECKING:
    from mopidy.backend import BackendProxy
    from mopidy.core.actor import Backends, Core

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _backend_error_handling(
    backend: BackendProxy,
    reraise: None | (type[Exception] | tuple[type[Exception], ...]) = None,
) -> Generator[None, Any, None]:
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
    def __init__(self, backends: Backends, core: Core) -> None:
        self.backends = backends
        self.core = core

    def _get_backend(self, uri: Uri) -> BackendProxy | None:
        uri_scheme = UriScheme(urllib.parse.urlparse(uri).scheme)
        return self.backends.with_library.get(uri_scheme, None)

    def _get_backends_to_uris(
        self,
        uris: Iterable[Uri] | None,
    ) -> dict[BackendProxy, list[Uri] | None]:
        if not uris:
            return dict.fromkeys(self.backends.with_library.values())

        result: dict[BackendProxy, list[Uri] | None] = collections.defaultdict(list)
        for uri in uris:
            backend = self._get_backend(uri)
            if backend is not None:
                lst = result[backend]
                assert lst is not None
                lst.append(uri)
        return result

    def browse(self, uri: Uri | None) -> list[Ref]:
        """Browse directories and tracks at the given ``uri``.

        ``uri`` is a string which represents some directory belonging to a
        backend. To get the initial root directories for backends pass
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

        :param uri: URI to browse

        .. versionadded:: 0.18
        """
        if uri is None:
            return self._roots()
        if not uri.strip():
            return []
        validation.check_uri(uri)
        return self._browse(uri)

    def _roots(self) -> list[Ref]:
        directories = set()
        backends = self.backends.with_library_browse.values()
        futures = {b: b.library.root_directory for b in backends}
        for backend, future in futures.items():
            with _backend_error_handling(backend):
                root = future.get()
                validation.check_instance(root, Ref)
                directories.add(root)
        return sorted(directories, key=operator.attrgetter("name"))

    def _browse(self, uri: Uri) -> list[Ref]:
        scheme = UriScheme(urllib.parse.urlparse(uri).scheme)
        backend = self.backends.with_library_browse.get(scheme)

        if not backend:
            return []

        with _backend_error_handling(backend):
            result = backend.library.browse(uri).get()
            validation.check_instances(result, Ref)
            return result

        return []

    def get_distinct(
        self,
        field: DistinctField,
        query: Query[SearchField] | None = None,
    ) -> set[Any]:
        """List distinct values for a given field from the library.

        This has mainly been added to support the list commands the MPD
        protocol supports in a more sane fashion. Other frontends are not
        recommended to use this method.

        Returns set of values corresponding to the requested field type.

        :param field: Any one of ``uri``, ``track_name``, ``album``,
            ``artist``, ``albumartist``, ``composer``, ``performer``,
            ``track_no``, ``genre``, ``date``, ``comment``, ``disc_no``,
            ``musicbrainz_albumid``, ``musicbrainz_artistid``, or
            ``musicbrainz_trackid``.
        :param query: Query to use for limiting results, see
            :meth:`search` for details about the query format.

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
        if query is not None:
            validation.check_query(query)  # TODO: normalize?

        compat_field = cast(DistinctField, {"track_name": "track"}.get(field, field))

        result = set()
        futures = {
            b: b.library.get_distinct(compat_field, query)
            for b in self.backends.with_library.values()
        }
        for backend, future in futures.items():
            with _backend_error_handling(backend):
                values = future.get()
                if values is not None:
                    if field_type is not None:
                        validation.check_instances(values, field_type)
                    result.update(values)
        return result

    def get_images(self, uris: Iterable[Uri]) -> dict[Uri, tuple[Image, ...]]:
        """Lookup the images for the given URIs.

        Backends can use this to return image URIs for any URI they know about
        be it tracks, albums, playlists. The lookup result is a dictionary
        mapping the provided URIs to lists of images.

        Unknown URIs or URIs the corresponding backend couldn't find anything
        for will simply return an empty list for that URI.

        :param uris: list of URIs to find images for

        .. versionadded:: 1.0
        """
        validation.check_uris(uris)

        futures = {
            backend: backend.library.get_images(backend_uris)
            for (backend, backend_uris) in self._get_backends_to_uris(uris).items()
            if backend_uris
        }

        results: dict[Uri, tuple[Image, ...]] = dict.fromkeys(uris, ())
        for backend, future in futures.items():
            with _backend_error_handling(backend):
                if future.get() is None:
                    continue
                validation.check_instance(future.get(), Mapping)
                for uri, images in future.get().items():
                    if uri not in uris:
                        msg = f"Got unknown image URI: {uri}"
                        raise exceptions.ValidationError(msg)
                    validation.check_instances(images, Image)
                    results[uri] += tuple(images)
        return results

    def lookup(self, uris: Iterable[Uri]) -> dict[Uri, list[Track]]:
        """Lookup the given URIs.

        If the URI expands to multiple tracks, the returned list will contain
        them all.

        :param uris: track URIs
        """
        validation.check_uris(uris)

        futures = {
            backend: backend.library.lookup_many(backend_uris)
            for (backend, backend_uris) in self._get_backends_to_uris(uris).items()
            if backend_uris
        }
        results = {u: [] for u in uris}

        for backend, future in futures.items():
            with _backend_error_handling(backend):
                result = future.get()
                if result is not None:
                    validation.check_instance(result, Mapping)
                    for uri, tracks in result.items():
                        # TODO: Consider making Track.uri field mandatory, and
                        # then remove this filtering of tracks without URIs.
                        validation.check_instances(tracks, Track)
                        results[uri] = [track for track in tracks if track.uri]

        return results

    def refresh(self, uri: Uri | None = None) -> None:
        """Refresh library. Limit to URI and below if an URI is given.

        :param uri: directory or track URI
        """
        if uri is not None:
            validation.check_uri(uri)

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

    def search(
        self,
        query: Query[SearchField],
        uris: Iterable[Uri] | None = None,
        exact: bool = False,
    ) -> list[SearchResult]:
        """Search the library for tracks where ``field`` contains ``values``.

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
        :param uris: zero or more URI roots to limit the search to
        :param exact: if the search should use exact matching

        .. versionadded:: 1.0
            The ``exact`` keyword argument.
        """
        query = _normalize_query(query)

        if uris is not None:
            validation.check_uris(uris)
        validation.check_query(query)
        validation.check_boolean(exact)

        if not query:
            return []

        futures = {}
        for backend, backend_uris in self._get_backends_to_uris(uris).items():
            futures[backend] = backend.library.search(
                query=query,
                uris=backend_uris,
                exact=exact,
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
                        validation.check_instance(result, SearchResult)
                        results.append(result)
            except TypeError:
                backend_name = backend.actor_ref.actor_class.__name__
                logger.warning(
                    '%s does not implement library.search() with "exact" '
                    "support. Please upgrade it.",
                    backend_name,
                )

        return results


def _normalize_query(query: Query[SearchField]) -> Query[SearchField]:
    broken_client = False
    # TODO: this breaks if query is not a dictionary like object...
    for field, values in query.items():
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
            "and file a bug.",
        )
    return query


class LibraryControllerProxy:
    browse = proxy_method(LibraryController.browse)
    get_distinct = proxy_method(LibraryController.get_distinct)
    get_images = proxy_method(LibraryController.get_images)
    lookup = proxy_method(LibraryController.lookup)
    refresh = proxy_method(LibraryController.refresh)
    search = proxy_method(LibraryController.search)
