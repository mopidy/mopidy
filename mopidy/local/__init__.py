from __future__ import absolute_import, unicode_literals

import logging
import os

import mopidy
from mopidy import config, ext, models

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local'
    ext_name = 'local'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['library'] = config.String()
        schema['media_dir'] = config.Path()
        schema['data_dir'] = config.Deprecated()
        schema['playlists_dir'] = config.Deprecated()
        schema['tag_cache_file'] = config.Deprecated()
        schema['scan_timeout'] = config.Integer(
            minimum=1000, maximum=1000 * 60 * 60)
        schema['scan_flush_threshold'] = config.Integer(minimum=0)
        schema['scan_follow_symlinks'] = config.Boolean()
        schema['excluded_file_extensions'] = config.List(optional=True)
        return schema

    def setup(self, registry):
        from .actor import LocalBackend
        from .json import JsonLibrary

        LocalBackend.libraries = registry['local:library']

        registry.add('backend', LocalBackend)
        registry.add('local:library', JsonLibrary)

    def get_command(self):
        from .commands import LocalCommand
        return LocalCommand()


class Library(object):

    """
    Local library interface.

    Extensions that wish to provide an alternate local library storage backend
    need to sub-class this class and install and configure it with an
    extension. Both scanning and library calls will use the active local
    library.

    :param config: Config dictionary
    """

    ROOT_DIRECTORY_URI = 'local:directory'
    """
    URI of the local backend's root directory.

    This constant should be used by libraries implementing the
    :meth:`Library.browse` method.
    """

    #: Name of the local library implementation, must be overriden.
    name = None

    #: Feature marker to indicate that you want :meth:`add()` calls to be
    #: called with optional arguments tags and duration.
    add_supports_tags_and_duration = False

    def __init__(self, config):
        self._config = config

    def browse(self, uri):
        """
        Browse directories and tracks at the given URI.

        The URI for the root directory is a constant available at
        :attr:`Library.ROOT_DIRECTORY_URI`.

        :param string path: URI to browse.
        :rtype: List of :class:`~mopidy.models.Ref` tracks and directories.
        """
        raise NotImplementedError

    def get_distinct(self, field, query=None):
        """
        List distinct values for a given field from the library.

        :param string field: One of ``artist``, ``albumartist``, ``album``,
            ``composer``, ``performer``, ``date``or ``genre``.
        :param dict query: Query to use for limiting results, see
            :meth:`search` for details about the query format.
        :rtype: set of values corresponding to the requested field type.
        """
        return set()

    def get_images(self, uris):
        """
        Lookup the images for the given URIs.

        The default implementation will simply call :meth:`lookup` and
        try and use the album art for any tracks returned. Most local
        libraries should replace this with something smarter or simply
        return an empty dictionary.

        :param list uris: list of URIs to find images for
        :rtype: {uri: tuple of :class:`mopidy.models.Image`}
        """
        result = {}
        for uri in uris:
            image_uris = set()
            tracks = self.lookup(uri)
            # local libraries may return single track
            if isinstance(tracks, models.Track):
                tracks = [tracks]
            for track in tracks:
                if track.album and track.album.images:
                    image_uris.update(track.album.images)
            result[uri] = [models.Image(uri=u) for u in image_uris]
        return result

    def load(self):
        """
        (Re)load any tracks stored in memory, if any, otherwise just return
        number of available tracks currently available. Will be called at
        startup for both library and update use cases, so if you plan to store
        tracks in memory this is when the should be (re)loaded.

        :rtype: :class:`int` representing number of tracks in library.
        """
        return 0

    def lookup(self, uri):
        """
        Lookup the given URI.

        :param string uri: track URI
        :rtype: list of :class:`~mopidy.models.Track` (or single
            :class:`~mopidy.models.Track` for backward compatibility)
        """
        raise NotImplementedError

    # TODO: remove uris, replacing it with support in query language.
    # TODO: remove exact, replacing it with support in query language.
    def search(self, query=None, limit=100, offset=0, exact=False, uris=None):
        """
        Search the library for tracks where ``field`` contains ``values``.

        :param dict query: one or more queries to search for
        :param int limit: maximum number of results to return
        :param int offset: offset into result set to use.
        :param bool exact: whether to look for exact matches
        :param uris: zero or more URI roots to limit the search to
        :type uris: list of strings or :class:`None`
        :rtype: :class:`~mopidy.models.SearchResult`
        """
        raise NotImplementedError

    # TODO: add file browsing support.

    # Remaining methods are use for the update process.
    def begin(self):
        """
        Prepare library for accepting updates. Exactly what this means is
        highly implementation depended. This must however return an iterator
        that generates all tracks in the library for efficient scanning.

        :rtype: :class:`~mopidy.models.Track` iterator
        """
        raise NotImplementedError

    def add(self, track, tags=None, duration=None):
        """
        Add the given track to library. Optional args will only be added if
        :attr:`add_supports_tags_and_duration` has been set.

        :param track: Track to add to the library
        :type track: :class:`~mopidy.models.Track`
        :param tags: All the tags the scanner found for the media. See
            :mod:`mopidy.audio.utils` for details about the tags.
        :type tags: dictionary of tag keys with a list of values.
        :param duration: Duration of media in milliseconds or :class:`None` if
            unknown
        :type duration: :class:`int` or :class:`None`
        """
        raise NotImplementedError

    def remove(self, uri):
        """
        Remove the given track from the library.

        :param str uri: URI to remove from the library/
        """
        raise NotImplementedError

    def flush(self):
        """
        Called for every n-th track indicating that work should be committed.
        Sub-classes are free to ignore these hints.

        :rtype: Boolean indicating if state was flushed.
        """
        return False

    def close(self):
        """
        Close any resources used for updating, commit outstanding work etc.
        """
        pass

    def clear(self):
        """
        Clear out whatever data storage is used by this backend.

        :rtype: Boolean indicating if state was cleared.
        """
        return False
