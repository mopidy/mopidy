from __future__ import absolute_import, unicode_literals

import contextlib
import logging

from mopidy import exceptions
from mopidy.compat import urllib
from mopidy.core import listener
from mopidy.internal import validation
from mopidy.models import Playlist, Ref

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _backend_error_handling(backend, reraise=None):
    try:
        yield
    except exceptions.ValidationError as e:
        logger.error('%s backend returned bad data: %s',
                     backend.actor_ref.actor_class.__name__, e)
    except Exception as e:
        if reraise and isinstance(e, reraise):
            raise
        logger.exception('%s backend caused an exception.',
                         backend.actor_ref.actor_class.__name__)


class PlaylistsController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def get_uri_schemes(self):
        """
        Get the list of URI schemes that support playlists.

        :rtype: list of string

        .. versionadded:: 2.0
        """
        return list(sorted(self.backends.with_playlists.keys()))

    def as_list(self):
        """
        Get a list of the currently available playlists.

        Returns a list of :class:`~mopidy.models.Ref` objects referring to the
        playlists. In other words, no information about the playlists' content
        is given.

        :rtype: list of :class:`mopidy.models.Ref`

        .. versionadded:: 1.0
        """
        futures = {
            backend: backend.playlists.as_list()
            for backend in set(self.backends.with_playlists.values())}

        results = []
        for b, future in futures.items():
            try:
                with _backend_error_handling(b, reraise=NotImplementedError):
                    playlists = future.get()
                    if playlists is not None:
                        validation.check_instances(playlists, Ref)
                        results.extend(playlists)
            except NotImplementedError:
                backend_name = b.actor_ref.actor_class.__name__
                logger.warning(
                    '%s does not implement playlists.as_list(). '
                    'Please upgrade it.', backend_name)

        return results

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
        validation.check_uri(uri)

        uri_scheme = urllib.parse.urlparse(uri).scheme
        backend = self.backends.with_playlists.get(uri_scheme, None)

        if not backend:
            return None

        with _backend_error_handling(backend):
            items = backend.playlists.get_items(uri).get()
            items is None or validation.check_instances(items, Ref)
            return items

        return None

    def create(self, name, uri_scheme=None):
        """
        Create a new playlist.

        If ``uri_scheme`` matches an URI scheme handled by a current backend,
        that backend is asked to create the playlist. If ``uri_scheme`` is
        :class:`None` or doesn't match a current backend, the first backend is
        asked to create the playlist.

        All new playlists must be created by calling this method, and **not**
        by creating new instances of :class:`mopidy.models.Playlist`.

        :param name: name of the new playlist
        :type name: string
        :param uri_scheme: use the backend matching the URI scheme
        :type uri_scheme: string
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        if uri_scheme in self.backends.with_playlists:
            backends = [self.backends.with_playlists[uri_scheme]]
        else:
            backends = self.backends.with_playlists.values()

        for backend in backends:
            with _backend_error_handling(backend):
                result = backend.playlists.create(name).get()
                if result is None:
                    continue
                validation.check_instance(result, Playlist)
                listener.CoreListener.send('playlist_changed', playlist=result)
                return result

        return None

    def delete(self, uri):
        """
        Delete playlist identified by the URI.

        If the URI doesn't match the URI schemes handled by the current
        backends, nothing happens.

        Returns :class:`True` if deleted, :class:`False` otherwise.

        :param uri: URI of the playlist to delete
        :type uri: string
        :rtype: :class:`bool`

        .. versionchanged:: 2.2
            Return type defined.
        """
        validation.check_uri(uri)

        uri_scheme = urllib.parse.urlparse(uri).scheme
        backend = self.backends.with_playlists.get(uri_scheme, None)
        if not backend:
            return False

        success = False
        with _backend_error_handling(backend):
            success = backend.playlists.delete(uri).get()

        if success is None:
            # Return type was defined in Mopidy 2.2. Assume everything went
            # well if the backend doesn't report otherwise.
            success = True

        if success:
            listener.CoreListener.send('playlist_deleted', uri=uri)

        return success

    def lookup(self, uri):
        """
        Lookup playlist with given URI in both the set of playlists and in any
        other playlist sources. Returns :class:`None` if not found.

        :param uri: playlist URI
        :type uri: string
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        uri_scheme = urllib.parse.urlparse(uri).scheme
        backend = self.backends.with_playlists.get(uri_scheme, None)
        if not backend:
            return None

        with _backend_error_handling(backend):
            playlist = backend.playlists.lookup(uri).get()
            playlist is None or validation.check_instance(playlist, Playlist)
            return playlist

        return None

    # TODO: there is an inconsistency between library.refresh(uri) and this
    # call, not sure how to sort this out.
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
        # TODO: check: uri_scheme is None or uri_scheme?

        futures = {}
        backends = {}
        playlists_loaded = False

        for backend_scheme, backend in self.backends.with_playlists.items():
            backends.setdefault(backend, set()).add(backend_scheme)

        for backend, backend_schemes in backends.items():
            if uri_scheme is None or uri_scheme in backend_schemes:
                futures[backend] = backend.playlists.refresh()

        for backend, future in futures.items():
            with _backend_error_handling(backend):
                future.get()
                playlists_loaded = True

        if playlists_loaded:
            listener.CoreListener.send('playlists_loaded')

    def save(self, playlist):
        """
        Save the playlist.

        For a playlist to be saveable, it must have the ``uri`` attribute set.
        You must not set the ``uri`` atribute yourself, but use playlist
        objects returned by :meth:`create` or retrieved from :attr:`playlists`,
        which will always give you saveable playlists.

        The method returns the saved playlist. The return playlist may differ
        from the saved playlist. E.g. if the playlist name was changed, the
        returned playlist may have a different URI. The caller of this method
        must throw away the playlist sent to this method, and use the
        returned playlist instead.

        If the playlist's URI isn't set or doesn't match the URI scheme of a
        current backend, nothing is done and :class:`None` is returned.

        :param playlist: the playlist
        :type playlist: :class:`mopidy.models.Playlist`
        :rtype: :class:`mopidy.models.Playlist` or :class:`None`
        """
        validation.check_instance(playlist, Playlist)

        if playlist.uri is None:
            return  # TODO: log this problem?

        uri_scheme = urllib.parse.urlparse(playlist.uri).scheme
        backend = self.backends.with_playlists.get(uri_scheme, None)
        if not backend:
            return None

        # TODO: we let AssertionError error through due to legacy tests :/
        with _backend_error_handling(backend, reraise=AssertionError):
            playlist = backend.playlists.save(playlist).get()
            playlist is None or validation.check_instance(playlist, Playlist)
            if playlist:
                listener.CoreListener.send(
                    'playlist_changed', playlist=playlist)
            return playlist

        return None
