from __future__ import unicode_literals

import urlparse


class MetadataController(object):
    pykka_traversable = True

    def __init__(self, backends, core):
        self.backends = backends
        self.core = core

    def _get_backend(self, uri):
        uri_scheme = urlparse.urlparse(uri).scheme
        return self.backends.with_library_by_uri_scheme.get(uri_scheme, None)

    def get(self, uri, key=None):
        backend = self._get_backend(uri)
        if backend and backend.has_metadata().get():
            return backend.metadata.get(uri, key).get()
        return {}

    def set(self, uri, key, value):
        backend = self._get_backend(uri)
        if backend and backend.has_metadata().get():
            return backend.metadata.set(uri, key, value).get()
        return {}
