class LibraryController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def find_exact(self, **query):
        """
        Search the library for tracks where ``field`` is ``values``.

        Examples::

            # Returns results matching 'a'
            find_exact(any=['a'])
            # Returns results matching artist 'xyz'
            find_exact(artist=['xyz'])
            # Returns results matching 'a' and 'b' and artist 'xyz'
            find_exact(any=['a', 'b'], artist=['xyz'])

        :param query: one or more queries to search for
        :type query: dict
        :rtype: :class:`mopidy.models.Playlist`
        """
        return self.backends[0].library.find_exact(**query).get()

    def lookup(self, uri):
        """
        Lookup track with given URI. Returns :class:`None` if not found.

        :param uri: track URI
        :type uri: string
        :rtype: :class:`mopidy.models.Track` or :class:`None`
        """
        return self.backends[0].library.lookup(uri).get()

    def refresh(self, uri=None):
        """
        Refresh library. Limit to URI and below if an URI is given.

        :param uri: directory or track URI
        :type uri: string
        """
        return self.backends[0].library.refresh(uri).get()

    def search(self, **query):
        """
        Search the library for tracks where ``field`` contains ``values``.

        Examples::

            # Returns results matching 'a'
            search(any=['a'])
            # Returns results matching artist 'xyz'
            search(artist=['xyz'])
            # Returns results matching 'a' and 'b' and artist 'xyz'
            search(any=['a', 'b'], artist=['xyz'])

        :param query: one or more queries to search for
        :type query: dict
        :rtype: :class:`mopidy.models.Playlist`
        """
        return self.backends[0].library.search(**query).get()
