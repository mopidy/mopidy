from __future__ import annotations

from typing import TYPE_CHECKING

import pykka
from pykka.typing import proxy_method

if TYPE_CHECKING:
    from mopidy.models import Playlist, Ref
    from mopidy.types import Uri

    from ._backend import Backend


@pykka.traversable
class PlaylistsProvider:
    """A playlist provider exposes a collection of playlists.

    The methods can create/change/delete playlists in this collection, and
    lookup of any playlist the backend knows about.

    :param backend: backend the controller is a part of
    """

    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    def as_list(self) -> list[Ref]:
        """Get a list of the currently available playlists.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlists. In other words, no information about the playlists' content
        is given.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def get_items(self, uri: Uri) -> list[Ref] | None:
        """Get the items in a playlist specified by ``uri``.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlist's items.

        If a playlist with the given ``uri`` doesn't exist, it returns
        :class:`None`.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def create(self, name: str) -> Playlist | None:
        """Create a new empty playlist with the given name.

        Returns a new playlist with the given name and an URI, or :class:`None`
        on failure.

        *MUST be implemented by subclass.*

        :param name: name of the new playlist
        """
        raise NotImplementedError

    def delete(self, uri: Uri) -> bool:
        """Delete playlist identified by the URI.

        Returns :class:`True` if deleted, :class:`False` otherwise.

        *MUST be implemented by subclass.*

        :param uri: URI of the playlist to delete

        .. versionchanged:: 2.2
            Return type defined.
        """
        raise NotImplementedError

    def lookup(self, uri: Uri) -> Playlist | None:
        """Lookup playlist with given URI in both the set of playlists and in any
        other playlist source.

        Returns the playlists or :class:`None` if not found.

        *MUST be implemented by subclass.*

        :param uri: playlist URI
        """
        raise NotImplementedError

    def refresh(self) -> None:
        """Refresh the playlists in :attr:`playlists`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def save(self, playlist: Playlist) -> Playlist | None:
        """Save the given playlist.

        The playlist must have an ``uri`` attribute set. To create a new
        playlist with an URI, use :meth:`create`.

        Returns the saved playlist or :class:`None` on failure.

        *MUST be implemented by subclass.*

        :param playlist: the playlist to save
        """
        raise NotImplementedError


class PlaylistsProviderProxy:
    as_list = proxy_method(PlaylistsProvider.as_list)
    get_items = proxy_method(PlaylistsProvider.get_items)
    create = proxy_method(PlaylistsProvider.create)
    delete = proxy_method(PlaylistsProvider.delete)
    lookup = proxy_method(PlaylistsProvider.lookup)
    refresh = proxy_method(PlaylistsProvider.refresh)
    save = proxy_method(PlaylistsProvider.save)
