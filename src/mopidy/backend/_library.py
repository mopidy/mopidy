# ruff: noqa: ARG002

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import pykka
from pykka.typing import proxy_field, proxy_method

if TYPE_CHECKING:
    from mopidy.models import Image, Ref, SearchResult, Track
    from mopidy.types import DistinctField, Query, SearchField, Uri

    from ._backend import Backend


@pykka.traversable
class LibraryProvider:
    """A library provider provides a library of music to Mopidy.

    :param backend: backend the controller is a part of
    """

    root_directory: Ref | None = None
    """
    :class:`mopidy.models.Ref.directory` instance with a URI and name set
    representing the root of this library's browse tree. URIs must
    use one of the schemes supported by the backend, and name should
    be set to a human friendly value.

    *MUST be set by any class that implements* :meth:`LibraryProvider.browse`.
    """

    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    def browse(self, uri: Uri) -> list[Ref]:
        """See :meth:`mopidy.core.LibraryController.browse`.

        If you implement this method, make sure to also set
        :attr:`root_directory`.

        *MAY be implemented by subclass.*
        """
        return []

    def get_distinct(
        self,
        field: DistinctField,
        query: Query[SearchField] | None = None,
    ) -> set[str]:
        """See :meth:`mopidy.core.LibraryController.get_distinct`.

        *MAY be implemented by subclass.*

        Default implementation will simply return an empty set.

        Note that backends should always return an empty set for unexpected
        field types.
        """
        return set()

    def get_images(self, uris: list[Uri]) -> dict[Uri, list[Image]]:
        """See :meth:`mopidy.core.LibraryController.get_images`.

        *MAY be implemented by subclass.*

        Default implementation will simply return an empty dictionary.
        """
        return {}

    def lookup_many(self, uris: Iterable[Uri]) -> dict[Uri, list[Track]]:
        """See :meth:`mopidy.core.LibraryController.lookup`.

        *MUST be implemented by subclass.*
        """
        return {uri: self.lookup(uri) for uri in uris}

    def lookup(self, uri: Uri) -> list[Track]:
        """See :meth:`mopidy.core.LibraryController.lookup`.

        *MUST be implemented by subclass if :meth:`lookup_many` is not implemented.*

        .. deprecated:: 4.0
            Implement :meth:`lookup_many` instead. If :meth:`lookup_many` is
            implemented, Mopidy will never call this method on a backend.
        """
        raise NotImplementedError

    def refresh(self, uri: Uri | None = None) -> None:
        """See :meth:`mopidy.core.LibraryController.refresh`.

        *MAY be implemented by subclass.*
        """

    def search(
        self,
        query: Query[SearchField],
        uris: list[Uri] | None = None,
        exact: bool = False,
    ) -> SearchResult | None:
        """See :meth:`mopidy.core.LibraryController.search`.

        *MAY be implemented by subclass.*

        .. versionadded:: 1.0
            The ``exact`` param which replaces the old ``find_exact``.
        """
        return None


class LibraryProviderProxy:
    root_directory = proxy_field(LibraryProvider.root_directory)
    browse = proxy_method(LibraryProvider.browse)
    get_distinct = proxy_method(LibraryProvider.get_distinct)
    get_images = proxy_method(LibraryProvider.get_images)
    lookup_many = proxy_method(LibraryProvider.lookup_many)
    lookup = proxy_method(LibraryProvider.lookup)
    refresh = proxy_method(LibraryProvider.refresh)
    search = proxy_method(LibraryProvider.search)
