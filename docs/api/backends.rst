*************************************
:mod:`mopidy.backends` -- Backend API
*************************************

.. warning::
    This is our *planned* backend API, and not the current API.

.. module:: mopidy.backends
    :synopsis: Interface between Mopidy and its various backends.

.. class:: BaseBackend()

    .. attribute:: current_playlist

        The current playlist controller. An instance of
        :class:`BaseCurrentPlaylistController`.

    .. attribute:: library

        The library controller. An instance of :class:`BaseLibraryController`.

    .. attribute:: playback

        The playback controller. An instance of :class:`BasePlaybackController`.

    .. attribute:: stored_playlists

        The stored playlists controller. An instance of
        :class:`BaseStoredPlaylistsController`.

    .. attribute:: uri_handlers

        List of URI prefixes this backend can handle.


.. class:: BaseCurrentPlaylistController(backend)

    :param backend: backend the controller is a part of
    :type backend: :class:`BaseBackend`

    .. method:: add(track, at_position=None)

        Add the track to the end of, or at the given position in the current
        playlist.

        :param track: track to add
        :type track: :class:`mopidy.models.Track`
        :param at_position: position in current playlist to add track
        :type at_position: int or :class:`None`

    .. method:: clear()

        Clear the current playlist.

    .. method:: load(playlist)

        Replace the current playlist with the given playlist.

        :param playlist: playlist to load
        :type playlist: :class:`mopidy.models.Playlist`

    .. method:: move(start, end, to_position)

        Move the tracks at positions in [``start``, ``end``] to
        ``to_position``.

        :param start: position of first track to move
        :type start: int
        :param end: position of last track to move
        :type end: int
        :param to_position: new position for the tracks
        :type to_position: int

    .. attribute:: playlist

        The currently loaded :class:`mopidy.models.Playlist`.

    .. method:: remove(track)

        Remove the track from the current playlist.

        :param track: track to remove
        :type track: :class:`mopidy.models.Track`

    .. method:: shuffle(start=None, end=None)

        Shuffles the playlist, optionally a part of the playlist given by
        ``start`` and ``end``.

        :param start: position of first track to shuffle
        :type start: int or :class:`None`
        :param end: position of last track to shuffle
        :type end: int or :class:`None`

    .. attribute:: version

        The current playlist version. Integer which is increased every time the
        current playlist is changed.


.. class:: BasePlaybackController(backend)

    :param backend: backend the controller is a part of
    :type backend: :class:`BaseBackend`

    .. attribute:: consume

        :class:`True`
            Tracks are removed from the playlist when they have been played.
        :class:`False`
            Tracks are not removed from the playlist.

    .. attribute:: current_track

        The currently playing or selected :class:`mopidy.models.Track`.

    .. method:: next()

        Play the next track.

    .. method:: pause()

        Pause playblack.

    .. attribute:: PAUSED

        Constant representing the paused state.

    .. method:: play(id=None, position=None)

        Play either the track with the given ID, the given position, or the
        currently active track.

        :param id: ID of track to play
        :type id: int
        :param position: position in current playlist of track to play
        :type position: int

    .. attribute:: PLAYING

        Constant representing the playing state.

    .. attribute:: playlist_position

        The position in the current playlist.

    .. method:: previous()

        Play the previous track.

    .. attribute:: random

        :class:`True`
            Tracks are selected at random from the playlist.
        :class:`False`
            Tracks are played in the order of the playlist.

    .. attribute:: repeat

        :class:`True`
            The current track is played repeatedly.
        :class:`False`
            The current track is played once.

    .. method:: resume()

        If paused, resume playing the current track.

    .. method:: seek(time_position)

        Seeks to time position given in milliseconds.

        :param time_position: time position in milliseconds
        :type time_position: int

    .. attribute:: state

        The playback state. Must be :attr:`PLAYING`, :attr:`PAUSED`, or
        :attr:`STOPPED`.

    .. method:: stop()

        Stop playing.

    .. attribute:: STOPPED

        Constant representing the stopped state.

    .. attribute:: time_position

        Time position in milliseconds.

    .. attribute:: volume

        The audio volume as an int in the range [0, 100]. :class:`None` if
        unknown.


.. class:: BaseLibraryController(backend)

    :param backend: backend the controller is a part of
    :type backend: :class:`BaseBackend`

    .. method:: find_exact(type, query)

        Find tracks in the library where ``type`` matches ``query`` exactly.

        :param type: 'title', 'artist', or 'album'
        :type type: string
        :param query: the search query
        :type query: string
        :rtype: list of :class:`mopidy.models.Track`

    .. method:: lookup(uri)

        Lookup track with given URI.

        :param uri: track URI
        :type uri: string
        :rtype: :class:`mopidy.models.Track`

    .. method:: refresh(uri=None)

        Refresh library. Limit to URI and below if an URI is given.

        :param uri: directory or track URI
        :type uri: string

    .. method:: search(type, query)

        Search the library for tracks where ``type`` contains ``query``.

        :param type: 'title', 'artist', 'album', or 'uri'
        :type type: string
        :param query: the search query
        :type query: string
        :rtype: list of :class:`mopidy.models.Track`


.. class:: BaseStoredPlaylistsController(backend)

    :param backend: backend the controller is a part of
    :type backend: :class:`BaseBackend`

    .. method:: add(uri)

        Add existing playlist with the given URI.

        :param uri: URI of existing playlist
        :type uri: string

    .. method:: create(name)

        Create a new playlist.

        :param name: name of the new playlist
        :type name: string
        :rtype: :class:`mopidy.models.Playlist`

    .. attribute:: playlists

        List of :class:`mopidy.models.Playlist`.

    .. method:: delete(playlist)

        Delete playlist.

        :param playlist: the playlist to delete
        :type playlist: :class:`mopidy.models.Playlist`

    .. method:: lookup(uri)

        Lookup playlist with given URI.

        :param uri: playlist URI
        :type uri: string
        :rtype: :class:`mopidy.models.Playlist`

    .. method:: refresh()

        Refresh stored playlists.

    .. method:: rename(playlist, new_name)

        Rename playlist.

        :param playlist: the playlist
        :type playlist: :class:`mopidy.models.Playlist`
        :param new_name: the new name
        :type new_name: string

    .. method:: search(query)

        Search for playlists whose name contains ``query``.

        :param query: query to search for
        :type query: string
        :rtype: list of :class:`mopidy.models.Playlist`
