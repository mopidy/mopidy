from __future__ import annotations

import contextlib
import logging
import urllib.parse
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

from pykka.typing import proxy_method

from mopidy import exceptions
from mopidy.core import listener
from mopidy.internal import validation
from mopidy.models import Playlist, Ref
from mopidy.types import UriScheme

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mopidy.backend import BackendProxy
    from mopidy.core.actor import Backends, Core
    from mopidy.types import Uri


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


class PlaylistsController:
    def __init__(self, backends: Backends, core: Core) -> None:
        self.backends = backends
        self.core = core

    def get_uri_schemes(self) -> list[UriScheme]:
        """Get the list of URI schemes that support playlists.

        .. versionadded:: 2.0
        """
        return sorted(self.backends.with_playlists.keys())

    def as_list(self) -> list[Ref]:
        """Get a list of the currently available playlists.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlists. In other words, no information about the playlists' content
        is given.

        .. versionadded:: 1.0
        """
        futures = {
            backend: backend.playlists.as_list()
            for backend in set(self.backends.with_playlists.values())
        }

        results = []
        for b, future in futures.items():
            try:
                with _backend_error_handling(b, reraise=NotImplementedError):
                    playlists = future.get()
                    if playlists is not None:
                        validation.check_instances(playlists, Ref)
                        results.extend(playlists)
            except NotImplementedError:
                backend_name = b.actor_ref.actor_class.__name__
                logger.warning(
                    "%s does not implement playlists.as_list(). Please upgrade it.",
                    backend_name,
                )

        return results

    def get_items(self, uri: Uri) -> list[Ref] | None:
        """Get the items in a playlist specified by ``uri``.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlist's items.

        If a playlist with the given ``uri`` doesn't exist, it returns
        :class:`None`.

        .. versionadded:: 1.0
        """
        validation.check_uri(uri)

        uri_scheme = UriScheme(urllib.parse.urlparse(uri).scheme)
        backend = self.backends.with_playlists.get(uri_scheme, None)

        if not backend:
            return None

        with _backend_error_handling(backend):
            items = backend.playlists.get_items(uri).get()
            if items is not None:
                validation.check_instances(items, Ref)
            return items

        return None

    def create(
        self,
        name: str,
        uri_scheme: UriScheme | None = None,
    ) -> Playlist | None:
        """Create a new playlist.

        If ``uri_scheme`` matches an URI scheme handled by a current backend,
        that backend is asked to create the playlist. If ``uri_scheme`` is
        :class:`None` or doesn't match a current backend, the first backend is
        asked to create the playlist.

        All new playlists must be created by calling this method, and **not**
        by creating new instances of :class:`mopidy.models.Playlist`.

        :param name: name of the new playlist
        :param uri_scheme: use the backend matching the URI scheme
        """
        if uri_scheme in self.backends.with_playlists:
            assert uri_scheme is not None
            backends = [self.backends.with_playlists[uri_scheme]]
        else:
            backends = self.backends.with_playlists.values()

        for backend in backends:
            with _backend_error_handling(backend):
                result = backend.playlists.create(name).get()
                if result is None:
                    continue
                validation.check_instance(result, Playlist)
                listener.CoreListener.send("playlist_changed", playlist=result)
                return result

        return None

    def delete(self, uri: Uri) -> bool:
        """Delete playlist identified by the URI.

        If the URI doesn't match the URI schemes handled by the current
        backends, nothing happens.

        Returns :class:`True` if deleted, :class:`False` otherwise.

        :param uri: URI of the playlist to delete

        .. versionchanged:: 2.2
            Return type defined.
        """
        validation.check_uri(uri)

        uri_scheme = UriScheme(urllib.parse.urlparse(uri).scheme)
        backend = self.backends.with_playlists.get(uri_scheme, None)
        if not backend:
            return False

        success = False
        with _backend_error_handling(backend):
            success = backend.playlists.delete(uri).get()

        if success is None:
            # Return type was defined in Mopidy 2.2. Assume everything went
            # well if the backend doesn't report otherwise.
            success = True

        if success:
            listener.CoreListener.send("playlist_deleted", uri=uri)

        return success

    def lookup(self, uri: Uri) -> Playlist | None:
        """Lookup playlist with given URI in both the set of playlists and in any
        other playlist sources. Returns :class:`None` if not found.

        :param uri: playlist URI
        """
        uri_scheme = UriScheme(urllib.parse.urlparse(uri).scheme)
        backend = self.backends.with_playlists.get(uri_scheme, None)
        if not backend:
            return None

        with _backend_error_handling(backend):
            playlist = backend.playlists.lookup(uri).get()
            if playlist is not None:
                validation.check_instance(playlist, Playlist)
            return playlist

        return None

    # TODO: there is an inconsistency between library.refresh(uri) and this
    # call, not sure how to sort this out.
    def refresh(self, uri_scheme: UriScheme | None = None) -> None:
        """Refresh the playlists in :attr:`playlists`.

        If ``uri_scheme`` is :class:`None`, all backends are asked to refresh.
        If ``uri_scheme`` is an URI scheme handled by a backend, only that
        backend is asked to refresh. If ``uri_scheme`` doesn't match any
        current backend, nothing happens.

        :param uri_scheme: limit to the backend matching the URI scheme
        """
        # TODO: check: uri_scheme is None or uri_scheme?

        futures = {}
        backends = {}
        playlists_loaded = False

        for backend_scheme, backend in self.backends.with_playlists.items():
            backends.setdefault(backend, set()).add(backend_scheme)

        for backend, backend_schemes in backends.items():
            if uri_scheme is None or uri_scheme in backend_schemes:
                futures[backend] = backend.playlists.refresh()

        for backend, future in futures.items():
            with _backend_error_handling(backend):
                future.get()
                playlists_loaded = True

        if playlists_loaded:
            listener.CoreListener.send("playlists_loaded")

    def save(self, playlist: Playlist) -> Playlist | None:
        """Save the playlist.

        For a playlist to be saveable, it must have the ``uri`` attribute set.
        You must not set the ``uri`` attribute yourself, but use playlist
        objects returned by :meth:`create` or retrieved from :attr:`playlists`,
        which will always give you saveable playlists.

        The method returns the saved playlist. The return playlist may differ
        from the saved playlist. E.g. if the playlist name was changed, the
        returned playlist may have a different URI. The caller of this method
        must throw away the playlist sent to this method, and use the
        returned playlist instead.

        If the playlist's URI isn't set or doesn't match the URI scheme of a
        current backend, nothing is done and :class:`None` is returned.

        :param playlist: the playlist
        """
        validation.check_instance(playlist, Playlist)

        if playlist.uri is None:
            return None  # TODO: log this problem?

        uri_scheme = UriScheme(urllib.parse.urlparse(playlist.uri).scheme)
        backend = self.backends.with_playlists.get(uri_scheme, None)
        if not backend:
            return None

        # TODO: we let AssertionError error through due to legacy tests :/
        with _backend_error_handling(backend, reraise=AssertionError):
            result = backend.playlists.save(playlist).get()
            if result is not None:
                validation.check_instance(result, Playlist)
            if result:
                listener.CoreListener.send("playlist_changed", playlist=result)
            return result

        return None


class PlaylistsControllerProxy:
    get_uri_schemes = proxy_method(PlaylistsController.get_uri_schemes)
    as_list = proxy_method(PlaylistsController.as_list)
    get_items = proxy_method(PlaylistsController.get_items)
    create = proxy_method(PlaylistsController.create)
    delete = proxy_method(PlaylistsController.delete)
    lookup = proxy_method(PlaylistsController.lookup)
    refresh = proxy_method(PlaylistsController.refresh)
    save = proxy_method(PlaylistsController.save)
