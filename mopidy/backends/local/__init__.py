from __future__ import unicode_literals

import logging
import os

import mopidy
from mopidy import config, ext

logger = logging.getLogger('mopidy.backends.local')


class Extension(ext.Extension):

    dist_name = 'Mopidy-Local'
    ext_name = 'local'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['media_dir'] = config.Path()
        schema['data_dir'] = config.Path()
        schema['playlists_dir'] = config.Path()
        schema['tag_cache_file'] = config.Deprecated()
        schema['scan_timeout'] = config.Integer(
            minimum=1000, maximum=1000*60*60)
        schema['excluded_file_extensions'] = config.List(optional=True)
        return schema

    def get_backend_classes(self):
        from .actor import LocalBackend
        return [LocalBackend]

    def get_command(self):
        from .commands import LocalCommand
        return LocalCommand()


class Library(object):
    #: Name of the local library implementation.
    name = None

    def __init__(self, config):
        self._config = config

    def load(self):
        """
        Initialize whatever resources are needed for this library.

        This is where you load the tracks into memory, setup a database
        conection etc.

        :rtype: :class:`int` representing number of tracks in library.
        """
        return 0

    def add(self, track):
        """
        Add the given track to library.

        :param track: Track to add to the library/
        :type track: :class:`mopidy.models.Track`
        """
        raise NotImplementedError

    def remove(self, uri):
        """
        Remove the given track from the library.

        :param uri: URI to remove from the library/
        :type uri: string
        """
        raise NotImplementedError

    def commit(self):
        """
        Persist any changes to the library.

        This is where you write your data file to disk, commit transactions
        etc. depending on the requirements of your library implementation.
        """
        pass

    def lookup(self, uri):
        """
        Lookup the given URI.

        If the URI expands to multiple tracks, the returned list will contain
        them all.

        :param uri: track URI
        :type uri: string
        :rtype: list of :class:`mopidy.models.Track`
        """
        raise NotImplementedError

    # TODO: support case with returning all tracks?
    # TODO: remove uris?
    def search(self, query=None, exact=False, uris=None):
        """
        Search the library for tracks where ``field`` contains ``values``.

        :param query: one or more queries to search for
        :type query: dict
        :param exact: look for exact matches?
        :type query: boolean
        :param uris: zero or more URI roots to limit the search to
        :type uris: list of strings or :class:`None`
        :rtype: :class:`mopidy.models.SearchResult`
        """
        raise NotImplementedError
