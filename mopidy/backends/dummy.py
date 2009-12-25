from mopidy.backends.base import BaseBackend

class DummyBackend(BaseBackend):
    def url_handlers(self):
        return [u'dummy:']
