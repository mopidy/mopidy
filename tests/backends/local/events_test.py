from mopidy import settings
from mopidy.backends.local import LocalBackend

from tests import unittest, path_to_data_dir
from tests.backends.base import events


class LocalBackendEventsTest(events.BackendEventsTest, unittest.TestCase):
    backend_class = LocalBackend

    def setUp(self):
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('empty_tag_cache')
        super(LocalBackendEventsTest, self).setUp()

    def tearDown(self):
        super(LocalBackendEventsTest, self).tearDown()
        settings.runtime.clear()
