from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pykka
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

if TYPE_CHECKING:
    from mopidy.audio import AudioProxy
    from mopidy.types import UriScheme

    from ._library import LibraryProvider, LibraryProviderProxy
    from ._playback import PlaybackProvider, PlaybackProviderProxy
    from ._playlists import PlaylistsProvider, PlaylistsProviderProxy


class Backend:
    """Backend API.

    If the backend has problems during initialization it should raise
    :exc:`mopidy.exceptions.BackendError` with a descriptive error message.
    This will make Mopidy print the error message and exit so that the user can
    fix the issue.

    :param audio: actor proxy for the audio subsystem
    """

    #: Actor proxy to an instance of :class:`mopidy.audio.Audio`.
    #:
    #: Should be passed to the backend constructor as the kwarg ``audio``,
    #: which will then set this field.
    audio: AudioProxy

    #: The library provider. An instance of
    #: :class:`~mopidy.backend.LibraryProvider`, or :class:`None` if
    #: the backend doesn't provide a library.
    library: LibraryProvider | None = None

    #: The playback provider. An instance of
    #: :class:`~mopidy.backend.PlaybackProvider`, or :class:`None` if
    #: the backend doesn't provide playback.
    playback: PlaybackProvider | None = None

    #: The playlists provider. An instance of
    #: :class:`~mopidy.backend.PlaylistsProvider`, or class:`None` if
    #: the backend doesn't provide playlists.
    playlists: PlaylistsProvider | None = None

    #: List of URI schemes this backend can handle.
    uri_schemes: ClassVar[list[UriScheme]] = []

    # Because the providers is marked as pykka.traversable(), we can't get()
    # them from another actor, and need helper methods to check if the
    # providers are set or None.

    def has_library(self) -> bool:
        return self.library is not None

    def has_library_browse(self) -> bool:
        return self.library is not None and self.library.root_directory is not None

    def has_playback(self) -> bool:
        return self.playback is not None

    def has_playlists(self) -> bool:
        return self.playlists is not None

    def ping(self) -> bool:
        """Called to check if the actor is still alive."""
        return True


class BackendActor(pykka.ThreadingActor, Backend):
    pass


class BackendProxy(ActorMemberMixin, pykka.ActorProxy[BackendActor]):
    """Backend wrapped in a Pykka actor proxy."""

    library: LibraryProviderProxy
    playback: PlaybackProviderProxy
    playlists: PlaylistsProviderProxy
    uri_schemes = proxy_field(BackendActor.uri_schemes)
    has_library = proxy_method(BackendActor.has_library)
    has_library_browse = proxy_method(BackendActor.has_library_browse)
    has_playback = proxy_method(BackendActor.has_playback)
    has_playlists = proxy_method(BackendActor.has_playlists)
    ping = proxy_method(BackendActor.ping)
