from __future__ import absolute_import, unicode_literals

import logging

from mopidy import listener, models


logger = logging.getLogger(__name__)


class Backend(object):

    """Backend API

    If the backend has problems during initialization it should raise
    :exc:`mopidy.exceptions.BackendError` with a descriptive error message.
    This will make Mopidy print the error message and exit so that the user can
    fix the issue.

    :param config: the entire Mopidy configuration
    :type config: dict
    :param audio: actor proxy for the audio subsystem
    :type audio: :class:`pykka.ActorProxy` for :class:`mopidy.audio.Audio`
    """

    #: Actor proxy to an instance of :class:`mopidy.audio.Audio`.
    #:
    #: Should be passed to the backend constructor as the kwarg ``audio``,
    #: which will then set this field.
    audio = None

    #: The library provider. An instance of
    #: :class:`~mopidy.backend.LibraryProvider`, or :class:`None` if
    #: the backend doesn't provide a library.
    library = None

    #: The playback provider. An instance of
    #: :class:`~mopidy.backend.PlaybackProvider`, or :class:`None` if
    #: the backend doesn't provide playback.
    playback = None

    #: The playlists provider. An instance of
    #: :class:`~mopidy.backend.PlaylistsProvider`, or class:`None` if
    #: the backend doesn't provide playlists.
    playlists = None

    #: List of URI schemes this backend can handle.
    uri_schemes = []

    # Because the providers is marked as pykka_traversible, we can't get() them
    # from another actor, and need helper methods to check if the providers are
    # set or None.

    def has_library(self):
        return self.library is not None

    def has_library_browse(self):
        return self.has_library() and self.library.root_directory is not None

    def has_playback(self):
        return self.playback is not None

    def has_playlists(self):
        return self.playlists is not None

    def ping(self):
        """Called to check if the actor is still alive."""
        return True


class LibraryProvider(object):

    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backend.Backend`
    """

    pykka_traversable = True

    root_directory = None
    """
    :class:`mopidy.models.Ref.directory` instance with a URI and name set
    representing the root of this library's browse tree. URIs must
    use one of the schemes supported by the backend, and name should
    be set to a human friendly value.

    *MUST be set by any class that implements* :meth:`LibraryProvider.browse`.
    """

    def __init__(self, backend):
        self.backend = backend

    def browse(self, uri):
        """
        See :meth:`mopidy.core.LibraryController.browse`.

        If you implement this method, make sure to also set
        :attr:`root_directory`.

        *MAY be implemented by subclass.*
        """
        return []

    def get_distinct(self, field, query=None):
        """
        See :meth:`mopidy.core.LibraryController.get_distinct`.

        *MAY be implemented by subclass.*

        Default implementation will simply return an empty set.

        Note that backends should always return an empty set for unexpected
        field types.
        """
        return set()

    def get_images(self, uris):
        """
        See :meth:`mopidy.core.LibraryController.get_images`.

        *MAY be implemented by subclass.*

        Default implementation will simply call lookup and try and use the
        album art for any tracks returned. Most extensions should replace this
        with something smarter or simply return an empty dictionary.
        """
        result = {}
        for uri in uris:
            image_uris = set()
            for track in self.lookup(uri):
                if track.album and track.album.images:
                    image_uris.update(track.album.images)
            result[uri] = [models.Image(uri=u) for u in image_uris]
        return result

    def lookup(self, uri):
        """
        See :meth:`mopidy.core.LibraryController.lookup`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def refresh(self, uri=None):
        """
        See :meth:`mopidy.core.LibraryController.refresh`.

        *MAY be implemented by subclass.*
        """
        pass

    def search(self, query=None, uris=None, exact=False):
        """
        See :meth:`mopidy.core.LibraryController.search`.

        *MAY be implemented by subclass.*

        .. versionadded:: 1.0
            The ``exact`` param which replaces the old ``find_exact``.
        """
        pass


class PlaybackProvider(object):

    """
    :param audio: the audio actor
    :type audio: actor proxy to an instance of :class:`mopidy.audio.Audio`
    :param backend: the backend
    :type backend: :class:`mopidy.backend.Backend`
    """

    pykka_traversable = True

    def __init__(self, audio, backend):
        self.audio = audio
        self.backend = backend

    def pause(self):
        """
        Pause playback.

        *MAY be reimplemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.audio.pause_playback().get()

    def play(self):
        """
        Start playback.

        *MAY be reimplemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.audio.start_playback().get()

    def prepare_change(self):
        """
        Indicate that an URI change is about to happen.

        *MAY be reimplemented by subclass.*

        It is extremely unlikely it makes sense for any backends to override
        this. For most practical purposes it should be considered an internal
        call between backends and core that backend authors should not touch.
        """
        self.audio.prepare_change().get()

    def translate_uri(self, uri):
        """
        Convert custom URI scheme to real playable URI.

        *MAY be reimplemented by subclass.*

        This is very likely the *only* thing you need to override as a backend
        author. Typically this is where you convert any Mopidy specific URI
        to a real URI and then return it. If you can't convert the URI just
        return :class:`None`.

        :param uri: the URI to translate
        :type uri: string
        :rtype: string or :class:`None` if the URI could not be translated
        """
        return uri

    def change_track(self, track):
        """
        Swith to provided track.

        *MAY be reimplemented by subclass.*

        It is unlikely it makes sense for any backends to override
        this. For most practical purposes it should be considered an internal
        call between backends and core that backend authors should not touch.

        The default implementation will call :meth:`translate_uri` which
        is what you want to implement.

        :param track: the track to play
        :type track: :class:`mopidy.models.Track`
        :rtype: :class:`True` if successful, else :class:`False`
        """
        uri = self.translate_uri(track.uri)
        if uri != track.uri:
            logger.debug(
                'Backend translated URI from %s to %s', track.uri, uri)
        if not uri:
            return False
        self.audio.set_uri(uri).get()
        return True

    def resume(self):
        """
        Resume playback at the same time position playback was paused.

        *MAY be reimplemented by subclass.*

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.audio.start_playback().get()

    def seek(self, time_position):
        """
        Seek to a given time position.

        *MAY be reimplemented by subclass.*

        :param time_position: time position in milliseconds
        :type time_position: int
        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.audio.set_position(time_position).get()

    def stop(self):
        """
        Stop playback.

        *MAY be reimplemented by subclass.*

        Should not be used for tracking if tracks have been played or when we
        are done playing them.

        :rtype: :class:`True` if successful, else :class:`False`
        """
        return self.audio.stop_playback().get()

    def get_time_position(self):
        """
        Get the current time position in milliseconds.

        *MAY be reimplemented by subclass.*

        :rtype: int
        """
        return self.audio.get_position().get()


class PlaylistsProvider(object):

    """
    A playlist provider exposes a collection of playlists, methods to
    create/change/delete playlists in this collection, and lookup of any
    playlist the backend knows about.

    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backend.Backend` instance
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend

    def as_list(self):
        """
        Get a list of the currently available playlists.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlists. In other words, no information about the playlists' content
        is given.

        :rtype: list of :class:`mopidy.models.Ref`

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def get_items(self, uri):
        """
        Get the items in a playlist specified by ``uri``.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlist's items.

        If a playlist with the given ``uri`` doesn't exist, it returns
        :class:`None`.

        :rtype: list of :class:`mopidy.models.Ref`, or :class:`None`

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def create(self, name):
        """
        Create a new empty playlist with the given name.

        Returns a new playlist with the given name and an URI, or :class:`None`
        on failure.

        *MUST be implemented by subclass.*

        :param name: name of the new playlist
        :type name: string
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        raise NotImplementedError

    def delete(self, uri):
        """
        Delete playlist identified by the URI.

        *MUST be implemented by subclass.*

        :param uri: URI of the playlist to delete
        :type uri: string
        """
        raise NotImplementedError

    def lookup(self, uri):
        """
        Lookup playlist with given URI in both the set of playlists and in any
        other playlist source.

        Returns the playlists or :class:`None` if not found.

        *MUST be implemented by subclass.*

        :param uri: playlist URI
        :type uri: string
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        raise NotImplementedError

    def refresh(self):
        """
        Refresh the playlists in :attr:`playlists`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def save(self, playlist):
        """
        Save the given playlist.

        The playlist must have an ``uri`` attribute set. To create a new
        playlist with an URI, use :meth:`create`.

        Returns the saved playlist or :class:`None` on failure.

        *MUST be implemented by subclass.*

        :param playlist: the playlist to save
        :type playlist: :class:`mopidy.models.Playlist`
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        raise NotImplementedError


class BackendListener(listener.Listener):

    """
    Marker interface for recipients of events sent by the backend actors.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in a backend actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.

    Normally, only the Core actor should mix in this class.
    """

    @staticmethod
    def send(event, **kwargs):
        """Helper to allow calling of backend listener events"""
        listener.send(BackendListener, event, **kwargs)

    def playlists_loaded(self):
        """
        Called when playlists are loaded or refreshed.

        *MAY* be implemented by actor.
        """
        pass
