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

    #: The tracklist provider. An instance of
    #: :class:`~mopidy.backends.base.BasePlaylistsProvider`, or class:`None` if
    #: the backend doesn't provide tracklist additional control logic
    tracklist = None

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

    def has_tracklist(self):
        return self.tracklist is not None


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


class BaseTracklistProvider(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend

    def next_track(self, tracklist, tl_track):
        """
        Get the next track to be played if the user used next button. The
        Provider should be careful with all the tracklist states. See
        :meth:`mopidy.core.TracklistController.next_track` code to know which
        parameters to take care of.

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param tl_track: The track to have the next song's of
        :type tl_track: :class:`mopidy.models.TlTrack`
        :rtype: It should be a :class:`mopidy.models.TlTrack`, None if the
        intention is to tell there is no way to go onwards. For example under
        a continuous non-seekable stream. Or finally, any other datatype than
        :class:`mopidy.models.TlTrack` or None, which will denote that normal
        actions should be following.
        """
        return str()

    def previous_track(self, tracklist, tl_track):
        """
        Get the track to be played if the user used previous button. The
        Provider should be careful with all the tracklist states. See
        :meth:`mopidy.core.TracklistController.previous_track` code to know
        which parameters to take care of.

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param tl_track: The track to have the previous song's of
        :type tl_track: :class:`mopidy.models.TlTrack`
        :rtype: It should be a :class:`mopidy.models.TlTrack`, None if the
        intention is to tell there is no way to go backwards. For example under
        a continuous non-seekable stream. Or finally, any other datatype than
        :class:`mopidy.models.TlTrack` or None, which will denote that normal
        actions should be following.
        """
        return str()

    def eot_track(self, tracklist, tl_track):
        """
        Get the track to be played if the previous track ended naturally. The
        Provider should be careful with all the tracklist states. See
        :meth:`mopidy.core.TracklistController.eot_track` code to know
        which parameters to take care of.

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param tl_track: The track to have the next song's of
        :type tl_track: :class:`mopidy.models.TlTrack`
        :rtype: It should be a :class:`mopidy.models.TlTrack`, None if the
        intention is to tell there is no way to go onwards for example when the
        tracklist is finished. Or finally, any other datatype than
        :class:`mopidy.models.TlTrack` or None, which will denote that normal
        actions should be following.
        """
        return str()

    def add(self, tracklist, tracks=None, at_position=None, uri=None):
        """
        When adding a new song, the Provider may decide to add or replace
        :meth:`mopidy.core.TracklistController.add`.

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param tracks: tracks to add
        :type tracks: list of :class:`mopidy.models.Track`
        :param at_position: position in tracklist to add track
        :type at_position: int or :class:`None`
        :param uri: URI for tracks to add
        :type uri: string
        :rtype: It should be a list of :class:`mopidy.models.TlTrack`, pointing
        out which where actually the added songs. Anything else will be
        considered as that the Controller should be running standard behaviour
        """
        return None

    def move(self, tracklist, start, end, to_position):
        """
        When moving songs from one position to another, this method can be
        used to add or replace the logic into
        :meth:`mopidy.core.TracklistController.move`.

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param start: Where to move tracks from tracklist position start
        :type start: int
        :param end: Where to move tracks from tracklist position end
        :type end: int
        :rtype: In order to add some login before, the Provider must return
        False, to replace the logic, the Provider must return True.
        """
        return False

    def remove(self, tracklist, tl_tracks):
        """
        When revmoving a song list, more logic can be added before or replacing
        completelly the standard one in
        :meth:`mopidy.core.TracklistController.remove`

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param tl_tracks: The tracks we are trying to remove from the tracklist
        :type tl_tracks: list of :class:`mopidy.models.TlTrack`
        :rtype: It should be a list of :class:`mopidy.models.TlTrack`, pointing
        out which where actually the removed songs. Anything else will be
        considered as that the Controller should be running standard behaviour
        """
        return None

    def shuffle(self, tracklist, start, end):
        """
        When suffling a slice of the tracklist, more logic can be added before
         or replacing completelly the standard one in
        :meth:`mopidy.core.TracklistController.shuffle`

        :param tracklist: The instance of core's TracklistController
        :type tracklist: :class:`mopidy.core.TracklistController`
        :param start: Where to shuffle tracklist from
        :type start: int
        :param end: Where to shuffle tracklist to
        :type end: int
        :rtype: In order to add some login before, the Provider must return
        False, to replace the logic, the Provider must return True.
        """
        return False

    def mark_played(self, tracklist, tl_track):
        return None

    def mark_playing(self, tracklist, tl_track):
        return None

    def mark_unplayable(self, tracklist, tl_track):
        return None

    def mark_metadata(self, tracklist, tl_track, metadata):
        return None
