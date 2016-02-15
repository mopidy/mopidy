from __future__ import absolute_import, unicode_literals

import re

# TOOD: refactor this into a generic mapper that does not know about browse
# or playlists and then use one instance for each case?


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
        self._browse_name_from_uri = {}
        self._playlist_name_from_uri = {}

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

    def insert(self, name, uri, playlist=False):
        """
        Create a unique and MPD compatible name that maps to the given URI.
        """
        name = self._create_unique_name(name, uri)
        self._uri_from_name[name] = uri
        if playlist:
            self._playlist_name_from_uri[uri] = name
        else:
            self._browse_name_from_uri[uri] = name
        return name

    def uri_from_name(self, name):
        """
        Return the uri for the given MPD name.
        """
        return self._uri_from_name.get(name)

    def refresh_playlists_mapping(self):
        """
        Maintain map between playlists and unique playlist names to be used by
        MPD.
        """
        if self.core is None:
            return

        for playlist_ref in self.core.playlists.as_list().get():
            if not playlist_ref.name:
                continue
            name = self._invalid_playlist_chars.sub('|', playlist_ref.name)
            self.insert(name, playlist_ref.uri, playlist=True)

    def playlist_uri_from_name(self, name):
        """
        Helper function to retrieve a playlist URI from its unique MPD name.
        """
        if name not in self._uri_from_name:
            self.refresh_playlists_mapping()
        return self._uri_from_name.get(name)

    def playlist_name_from_uri(self, uri):
        """
        Helper function to retrieve the unique MPD playlist name from its URI.
        """
        if uri not in self._playlist_name_from_uri:
            self.refresh_playlists_mapping()
        return self._playlist_name_from_uri[uri]
