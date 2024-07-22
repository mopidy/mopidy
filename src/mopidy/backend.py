# ruff: noqa: ARG002

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, ClassVar

import pykka
from pykka.typing import ActorMemberMixin, proxy_field, proxy_method

from mopidy import listener

if TYPE_CHECKING:
    from mopidy.audio.actor import AudioProxy
    from mopidy.internal.gi import Gst
    from mopidy.models import Image, Playlist, Ref, SearchResult, Track
    from mopidy.types import (
        DistinctField,
        DurationMs,
        Query,
        SearchField,
        Uri,
        UriScheme,
    )


logger = logging.getLogger(__name__)


class Backend:
    """Backend API.

    If the backend has problems during initialization it should raise
    :exc:`mopidy.exceptions.BackendError` with a descriptive error message.
    This will make Mopidy print the error message and exit so that the user can
    fix the issue.

    :param config: the entire Mopidy configuration
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
        self, field: DistinctField, query: Query[SearchField] | None = None
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


@pykka.traversable
class PlaybackProvider:
    """A playback provider provides audio playback control.

    :param audio: the audio actor
    :param backend: the backend
    """

    def __init__(self, audio: AudioProxy, backend: Backend) -> None:
        self.audio = audio
        self.backend = backend

    def pause(self) -> bool:
        """Pause playback.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.pause_playback().get()

    def play(self) -> bool:
        """Start playback.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.start_playback().get()

    def prepare_change(self) -> None:
        """Indicate that an URI change is about to happen.

        *MAY be reimplemented by subclass.*

        It is extremely unlikely it makes sense for any backends to override
        this. For most practical purposes it should be considered an internal
        call between backends and core that backend authors should not touch.
        """
        self.audio.prepare_change().get()

    def translate_uri(self, uri: Uri) -> Uri | None:
        """Convert custom URI scheme to real playable URI.

        *MAY be reimplemented by subclass.*

        This is very likely the *only* thing you need to override as a backend
        author. Typically this is where you convert any Mopidy specific URI
        to a real URI and then return it. If you can't convert the URI just
        return :class:`None`.

        :param uri: the URI to translate
        """
        return uri

    def is_live(self, uri: Uri) -> bool:
        """Decide if the URI should be treated as a live stream or not.

        *MAY be reimplemented by subclass.*

        Playing a source as a live stream disables buffering, which reduces
        latency before playback starts, and discards data when paused.

        :param uri: the URI
        """
        return False

    def should_download(self, uri: Uri) -> bool:
        """Attempt progressive download buffering for the URI or not.

        *MAY be reimplemented by subclass.*

        When streaming a fixed length file, the entire file can be buffered
        to improve playback performance.

        :param uri: the URI
        """
        return False

    def on_source_setup(self, source: Gst.Element) -> None:
        """Called when a new GStreamer source is created, allowing us to configure
        the source. This runs in the audio thread so should not block.

        *MAY be reimplemented by subclass.*

        :param source: the GStreamer source element

        .. versionadded:: 3.4
        """

    def change_track(self, track: Track) -> bool:
        """Switch to provided track.

        *MAY be reimplemented by subclass.*

        It is unlikely it makes sense for any backends to override
        this. For most practical purposes it should be considered an internal
        call between backends and core that backend authors should not touch.

        The default implementation will call :meth:`translate_uri` which
        is what you want to implement.

        :param track: the track to play
        """
        if track.uri is None:
            return False
        uri = self.translate_uri(track.uri)
        if uri != track.uri:
            logger.debug("Backend translated URI from %s to %s", track.uri, uri)
        if uri is None:
            return False
        self.audio.set_source_setup_callback(self.on_source_setup).get()
        self.audio.set_uri(
            uri,
            live_stream=self.is_live(uri),
            download=self.should_download(uri),
        ).get()
        return True

    def resume(self) -> bool:
        """Resume playback at the same time position playback was paused.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.start_playback().get()

    def seek(self, time_position: DurationMs) -> bool:
        """Seek to a given time position.

        *MAY be reimplemented by subclass.*

        Returns :class:`True` if successful, else :class:`False`.

        :param time_position: time position in milliseconds
        """
        return self.audio.set_position(time_position).get()

    def stop(self) -> bool:
        """Stop playback.

        *MAY be reimplemented by subclass.*

        Should not be used for tracking if tracks have been played or when we
        are done playing them.

        Returns :class:`True` if successful, else :class:`False`.
        """
        return self.audio.stop_playback().get()

    def get_time_position(self) -> DurationMs:
        """Get the current time position in milliseconds.

        *MAY be reimplemented by subclass.*
        """
        return self.audio.get_position().get()


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


class BackendListener(listener.Listener):
    """Marker interface for recipients of events sent by the backend actors.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in a backend actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.

    Normally, only the Core actor should mix in this class.
    """

    @staticmethod
    def send(event: str, **kwargs: Any) -> None:
        """Helper to allow calling of backend listener events."""
        listener.send(BackendListener, event, **kwargs)

    def playlists_loaded(self) -> None:
        """Called when playlists are loaded or refreshed.

        *MAY* be implemented by actor.
        """


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


class LibraryProviderProxy:
    root_directory = proxy_field(LibraryProvider.root_directory)
    browse = proxy_method(LibraryProvider.browse)
    get_distinct = proxy_method(LibraryProvider.get_distinct)
    get_images = proxy_method(LibraryProvider.get_images)
    lookup_many = proxy_method(LibraryProvider.lookup_many)
    refresh = proxy_method(LibraryProvider.refresh)
    search = proxy_method(LibraryProvider.search)


class PlaybackProviderProxy:
    pause = proxy_method(PlaybackProvider.pause)
    play = proxy_method(PlaybackProvider.play)
    prepare_change = proxy_method(PlaybackProvider.prepare_change)
    translate_uri = proxy_method(PlaybackProvider.translate_uri)
    is_live = proxy_method(PlaybackProvider.is_live)
    should_download = proxy_method(PlaybackProvider.should_download)
    on_source_setup = proxy_method(PlaybackProvider.on_source_setup)
    change_track = proxy_method(PlaybackProvider.change_track)
    resume = proxy_method(PlaybackProvider.resume)
    seek = proxy_method(PlaybackProvider.seek)
    stop = proxy_method(PlaybackProvider.stop)
    get_time_position = proxy_method(PlaybackProvider.get_time_position)


class PlaylistsProviderProxy:
    as_list = proxy_method(PlaylistsProvider.as_list)
    get_items = proxy_method(PlaylistsProvider.get_items)
    create = proxy_method(PlaylistsProvider.create)
    delete = proxy_method(PlaylistsProvider.delete)
    lookup = proxy_method(PlaylistsProvider.lookup)
    refresh = proxy_method(PlaylistsProvider.refresh)
    save = proxy_method(PlaylistsProvider.save)
