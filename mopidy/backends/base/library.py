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
