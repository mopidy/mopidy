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
    look up any playlist the backend knows about.
    """

    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    def as_list(self) -> list[Ref]:
        """Get a list of the currently available playlists.

        Returns a list of [Ref][mopidy.models.Ref] objects referring to the
        playlists. In other words, no information about the playlists' content
        is given.
        """
        raise NotImplementedError

    def get_items(self, uri: Uri) -> list[Ref] | None:
        """Get the items in a playlist specified by `uri`.

        Returns a list of [Ref][mopidy.models.Ref] objects referring to the
        playlist's items, or `None` if the playlist doesn't exist.
        """
        raise NotImplementedError

    def create(self, name: str) -> Playlist | None:
        """Create a new empty playlist with the given name.

        Returns a new playlist with the given name and a URI, or `None` on
        failure.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def delete(self, uri: Uri) -> bool:
        """Delete playlist identified by the URI.

        Returns `True` if deleted, `False` otherwise.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def lookup(self, uri: Uri) -> Playlist | None:
        """Look up playlist with given URI.

        Searches both the set of playlists and any other playlist sources.
        Returns the playlist or `None` if not found.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def refresh(self) -> None:
        """Refresh the playlists.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def save(self, playlist: Playlist) -> Playlist | None:
        """Save the given playlist.

        The playlist must have a `uri` attribute set. To create a new playlist
        with a URI, use [create][].

        Returns the saved playlist or `None` on failure.

        *MUST be implemented by subclass.*
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
