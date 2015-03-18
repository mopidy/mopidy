from __future__ import absolute_import, unicode_literals

from mopidy import listener, models


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

    # TODO: replace with search(query, exact=True, ...)
    def find_exact(self, query=None, uris=None):
        """
        See :meth:`mopidy.core.LibraryController.find_exact`.

        *MAY be implemented by subclass.*
        """
        pass

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

    def search(self, query=None, uris=None):
        """
        See :meth:`mopidy.core.LibraryController.search`.

        *MAY be implemented by subclass.*
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

    def play(self, track):
        """
        Play given track.

        *MAY be reimplemented by subclass.*

        :param track: the track to play
        :type track: :class:`mopidy.models.Track`
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self.audio.prepare_change()
        self.change_track(track)
        return self.audio.start_playback().get()

    def change_track(self, track):
        """
        Swith to provided track.

        *MAY be reimplemented by subclass.*

        :param track: the track to play
        :type track: :class:`mopidy.models.Track`
        :rtype: :class:`True` if successful, else :class:`False`
        """
        self.audio.set_uri(track.uri).get()
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

    # TODO Replace playlists property with a get_playlists() method which
    # returns playlist Ref's instead of the gigantic data structures we
    # currently make available. lookup() should be used for getting full
    # playlists with all details.

    def get_playlists(self, ref=True):
        """
        Get available playlists.

        If ``ref`` is :class:`False`, a list of :class:`mopidy.models.Playlist`
        is returned.

        If ``ref`` is :class:`True`, a list of :class:`mopidy.models.Ref`
        referencing the playlists is returned.

        Implementors should use :class:`True` as the default value for the
        ``ref`` keyword argument.

        .. versionadded:: 0.20

        .. deprecated:: 0.20
            The ``ref`` keyword argument will be removed in the future together
            with the behavior associated with ``ref`` being :class:`False`.
        """
        if ref:
            return []
        else:
            return self.playlists

    @property
    def playlists(self):
        """
        Currently available playlists.

        Read/write. List of :class:`mopidy.models.Playlist`.

        .. deprecated:: 0.20
            If your backend requires Mopidy >= 0.20, implement
            :meth:`get_playlists` instead of this property. If you must stay
            compatible with Mopidy < 0.20, you're free to implement
            :meth:`get_playlists` in addition to this property.
        """
        return []

    @playlists.setter  # noqa
    def playlists(self, playlists):
        raise NotImplementedError

    def create(self, name):
        """
        Create a new empty playlist with the given name.

        Returns a new playlist with the given name and an URI.

        *MUST be implemented by subclass.*

        :param name: name of the new playlist
        :type name: string
        :rtype: :class:`mopidy.models.Playlist`
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
    defined here when the corresponding events happen in the core actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.

    Normally, only the Core actor should mix in this class.
    """

    @staticmethod
    def send(event, **kwargs):
        """Helper to allow calling of backend listener events"""
        listener.send_async(BackendListener, event, **kwargs)

    def playlists_loaded(self):
        """
        Called when playlists are loaded or refreshed.

        *MAY* be implemented by actor.
        """
        pass
