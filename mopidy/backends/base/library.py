import logging

logger = logging.getLogger('mopidy.backends.base')

class LibraryController(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    :param provider: provider the controller should use
    :type provider: instance of :class:`BaseLibraryProvider`
    """

    pykka_traversable = True

    def __init__(self, backend, provider):
        self.backend = backend
        self.provider = provider

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
        return self.provider.find_exact(**query)

    def lookup(self, uri):
        """
        Lookup track with given URI. Returns :class:`None` if not found.

        :param uri: track URI
        :type uri: string
        :rtype: :class:`mopidy.models.Track` or :class:`None`
        """
        return self.provider.lookup(uri)

    def refresh(self, uri=None):
        """
        Refresh library. Limit to URI and below if an URI is given.

        :param uri: directory or track URI
        :type uri: string
        """
        return self.provider.refresh(uri)

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
        return self.provider.search(**query)


class BaseLibraryProvider(object):
    """
    :param backend: backend the controller is a part of
    :type backend: :class:`mopidy.backends.base.Backend`
    """

    pykka_traversable = True

    def __init__(self, backend):
        self.backend = backend

    def find_exact(self, **query):
        """
        See :meth:`mopidy.backends.base.LibraryController.find_exact`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def lookup(self, uri):
        """
        See :meth:`mopidy.backends.base.LibraryController.lookup`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def refresh(self, uri=None):
        """
        See :meth:`mopidy.backends.base.LibraryController.refresh`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def search(self, **query):
        """
        See :meth:`mopidy.backends.base.LibraryController.search`.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError
