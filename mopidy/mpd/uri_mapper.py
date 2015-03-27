from __future__ import absolute_import, unicode_literals

import re


class MpdUriMapper(object):
    """
    Maintains the mappings between uniquified MPD names and URIs.
    """

    #: The Mopidy core API. An instance of :class:`mopidy.core.Core`.
    core = None

    _invalid_browse_chars = re.compile(r'[\n\r]')
    _invalid_playlist_chars = re.compile(r'[/]')

    def __init__(self, core=None):
        self.core = core
        self._uri_from_name = {}
        self._name_from_uri = {}

    def _create_unique_name(self, name, uri):
        stripped_name = self._invalid_browse_chars.sub(' ', name)
        name = stripped_name
        i = 2
        while name in self._uri_from_name:
            if self._uri_from_name[name] == uri:
                return name
            name = '%s [%d]' % (stripped_name, i)
            i += 1
        return name

    def insert(self, name, uri):
        """
        Create a unique and MPD compatible name that maps to the given URI.
        """
        name = self._create_unique_name(name, uri)
        self._uri_from_name[name] = uri
        self._name_from_uri[uri] = name
        return name

    def uri_from_name(self, name):
        """
        Return the uri for the given MPD name.
        """
        if name in self._uri_from_name:
            return self._uri_from_name[name]

    def refresh_playlists_mapping(self):
        """
        Maintain map between playlists and unique playlist names to be used by
        MPD.
        """
        if self.core is not None:
            for playlist_ref in self.core.playlists.as_list().get():
                if not playlist_ref.name:
                    continue
                name = self._invalid_playlist_chars.sub('|', playlist_ref.name)
                self.insert(name, playlist_ref.uri)

    def playlist_uri_from_name(self, name):
        """
        Helper function to retrieve a playlist URI from its unique MPD name.
        """
        if not self._uri_from_name:
            self.refresh_playlists_mapping()
        return self._uri_from_name.get(name)

    def playlist_name_from_uri(self, uri):
        """
        Helper function to retrieve the unique MPD playlist name from its URI.
        """
        if uri not in self._name_from_uri:
            self.refresh_playlists_mapping()
        return self._name_from_uri[uri]
