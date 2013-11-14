from __future__ import unicode_literals

import copy


class Backend(object):
    #: Actor proxy to an instance of :class:`mopidy.audio.Audio`.
    #:
    #: Should be passed to the backend constructor as the kwarg ``audio``,
    #: which will then set this field.
    audio = None

    #: The library provider. An instance of
    #: :class:`~mopidy.backends.base.BaseLibraryProvider`, or :class:`None` if
    #: the backend doesn't provide a library.
    library = None

    #: The playback provider. An instance of
    #: :class:`~mopidy.backends.base.BasePlaybackProvider`, or :class:`None` if
    #: the backend doesn't provide playback.
    playback = None

    #: The playlists provider. An instance of
    #: :class:`~mopidy.backends.base.BasePlaylistsProvider`, or class:`None` if
    #: the backend doesn't provide playlists.
    playlists = None

    #: List of URI schemes this backend can handle.
    uri_schemes = []

    # Because the providers is marked as pykka_traversible, we can't get() them
    # from another actor, and need helper methods to check if the providers are
    # set or None.

    def has_library(self):
        return self.library is not None

    def has_playback(self):
        return self.playback is not None

    def has_playlists(self):
        return self.playlists is not None


class BaseLibraryProvider(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend

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


class BaseLibraryUpdateProvider(object):
    uri_schemes = []

    def load(self):
        """Loads the library and returns all tracks in it.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def add(self, track):
        """Adds given track to library.

        Overwrites any existing track with same URI.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def remove(self, uri):
        """Removes given track from library.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def commit(self):
        """Persist changes to library.

        *MAY be implemented by subclass.*
        """
        pass


class BasePlaybackProvider(object):
    """
    :param audio: the audio actor
    :type audio: actor proxy to an instance of :class:`mopidy.audio.Audio`
    :param backend: the backend
    :type backend: :class:`mopidy.backends.base.Backend`
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


class BasePlaylistsProvider(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend
        self._playlists = []

    @property
    def playlists(self):
        """
        Currently available playlists.

        Read/write. List of :class:`mopidy.models.Playlist`.
        """
        return copy.copy(self._playlists)

    @playlists.setter  # noqa
    def playlists(self, playlists):
        self._playlists = playlists

    def create(self, name):
        """
        See :meth:`mopidy.core.PlaylistsController.create`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def delete(self, uri):
        """
        See :meth:`mopidy.core.PlaylistsController.delete`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def lookup(self, uri):
        """
        See :meth:`mopidy.core.PlaylistsController.lookup`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def refresh(self):
        """
        See :meth:`mopidy.core.PlaylistsController.refresh`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def save(self, playlist):
        """
        See :meth:`mopidy.core.PlaylistsController.save`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError
