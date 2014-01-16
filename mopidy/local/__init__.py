from __future__ import unicode_literals

import logging
import os

import mopidy
from mopidy import config, ext

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
        schema['data_dir'] = config.Path()
        schema['playlists_dir'] = config.Path()
        schema['tag_cache_file'] = config.Deprecated()
        schema['scan_timeout'] = config.Integer(
            minimum=1000, maximum=1000*60*60)
        schema['scan_flush_threshold'] = config.Integer(minimum=0)
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

    #: Name of the local library implementation, must be overriden.
    name = None

    def __init__(self, config):
        self._config = config

    def browse(self, path):
        """
        Browse directories and tracks at the given path.

        :param string path: path to browse or None for root.
        :rtype: List of :class:`~mopidy.models.Ref` tracks and directories.
        """
        raise NotImplementedError

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

        Unlike the core APIs, local tracks uris can only be resolved to a
        single track.

        :param string uri: track URI
        :rtype: :class:`~mopidy.models.Track`
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

    def add(self, track):
        """
        Add the given track to library.

        :param track: Track to add to the library
        :type track: :class:`~mopidy.models.Track`
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
