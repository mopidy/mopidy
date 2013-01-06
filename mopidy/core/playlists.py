from __future__ import unicode_literals

import itertools
import urlparse

import pykka

from . import listener


class PlaylistsController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def get_playlists(self, include_tracks=True):
        futures = [
            b.playlists.playlists for b in self.backends.with_playlists]
        results = pykka.get_all(futures)
        playlists = list(itertools.chain(*results))
        if not include_tracks:
            playlists = [p.copy(tracks=[]) for p in playlists]
        return playlists

    playlists = property(get_playlists)
    """
    The available playlists.

    Read-only. List of :class:`mopidy.models.Playlist`.
    """

    def create(self, name, uri_scheme=None):
        """
        Create a new playlist.

        If ``uri_scheme`` matches an URI scheme handled by a current backend,
        that backend is asked to create the playlist. If ``uri_scheme`` is
        :class:`None` or doesn't match a current backend, the first backend is
        asked to create the playlist.

        All new playlists should be created by calling this method, and **not**
        by creating new instances of :class:`mopidy.models.Playlist`.

        :param name: name of the new playlist
        :type name: string
        :param uri_scheme: use the backend matching the URI scheme
        :type uri_scheme: string
        :rtype: :class:`mopidy.models.Playlist`
        """
        if uri_scheme in self.backends.with_playlists_by_uri_scheme:
            backend = self.backends.by_uri_scheme[uri_scheme]
        else:
            backend = self.backends.with_playlists[0]
        playlist = backend.playlists.create(name).get()
        listener.CoreListener.send('playlist_changed', playlist=playlist)
        return playlist

    def delete(self, uri):
        """
        Delete playlist identified by the URI.

        If the URI doesn't match the URI schemes handled by the current
        backends, nothing happens.

        :param uri: URI of the playlist to delete
        :type uri: string
        """
        uri_scheme = urlparse.urlparse(uri).scheme
        backend = self.backends.with_playlists_by_uri_scheme.get(
            uri_scheme, None)
        if backend:
            backend.playlists.delete(uri).get()

    def filter(self, criteria=None, **kwargs):
        """
        Filter playlists by the given criterias.

        Examples::

            # Returns track with name 'a'
            filter({'name': 'a'})
            filter(name='a')

            # Returns track with URI 'xyz'
            filter({'uri': 'xyz'})
            filter(uri='xyz')

            # Returns track with name 'a' and URI 'xyz'
            filter({'name': 'a', 'uri': 'xyz'})
            filter(name='a', uri='xyz')

        :param criteria: one or more criteria to match by
        :type criteria: dict
        :rtype: list of :class:`mopidy.models.Playlist`
        """
        criteria = criteria or kwargs
        matches = self.playlists
        for (key, value) in criteria.iteritems():
            matches = filter(lambda p: getattr(p, key) == value, matches)
        return matches

    def lookup(self, uri):
        """
        Lookup playlist with given URI in both the set of playlists and in any
        other playlist sources. Returns :class:`None` if not found.

        :param uri: playlist URI
        :type uri: string
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        uri_scheme = urlparse.urlparse(uri).scheme
        backend = self.backends.with_playlists_by_uri_scheme.get(
            uri_scheme, None)
        if backend:
            return backend.playlists.lookup(uri).get()
        else:
            return None

    def refresh(self, uri_scheme=None):
        """
        Refresh the playlists in :attr:`playlists`.

        If ``uri_scheme`` is :class:`None`, all backends are asked to refresh.
        If ``uri_scheme`` is an URI scheme handled by a backend, only that
        backend is asked to refresh. If ``uri_scheme`` doesn't match any
        current backend, nothing happens.

        :param uri_scheme: limit to the backend matching the URI scheme
        :type uri_scheme: string
        """
        if uri_scheme is None:
            futures = [
                b.playlists.refresh() for b in self.backends.with_playlists]
            pykka.get_all(futures)
            listener.CoreListener.send('playlists_loaded')
        else:
            backend = self.backends.with_playlists_by_uri_scheme.get(
                uri_scheme, None)
            if backend:
                backend.playlists.refresh().get()
                listener.CoreListener.send('playlists_loaded')

    def save(self, playlist):
        """
        Save the playlist.

        For a playlist to be saveable, it must have the ``uri`` attribute set.
        You should not set the ``uri`` atribute yourself, but use playlist
        objects returned by :meth:`create` or retrieved from :attr:`playlists`,
        which will always give you saveable playlists.

        The method returns the saved playlist. The return playlist may differ
        from the saved playlist. E.g. if the playlist name was changed, the
        returned playlist may have a different URI. The caller of this method
        should throw away the playlist sent to this method, and use the
        returned playlist instead.

        If the playlist's URI isn't set or doesn't match the URI scheme of a
        current backend, nothing is done and :class:`None` is returned.

        :param playlist: the playlist
        :type playlist: :class:`mopidy.models.Playlist`
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        if playlist.uri is None:
            return
        uri_scheme = urlparse.urlparse(playlist.uri).scheme
        backend = self.backends.with_playlists_by_uri_scheme.get(
            uri_scheme, None)
        if backend:
            playlist = backend.playlists.save(playlist).get()
            listener.CoreListener.send('playlist_changed', playlist=playlist)
            return playlist
