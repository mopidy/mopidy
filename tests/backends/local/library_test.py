from __future__ import unicode_literals

from mopidy import settings
from mopidy.backends.local import LocalBackend

from tests import unittest, path_to_data_dir
from tests.backends.base.library import LibraryControllerTest


class LocalLibraryControllerTest(LibraryControllerTest, unittest.TestCase):

    backend_class = LocalBackend

    def setUp(self):
        settings.LOCAL_TAG_CACHE_FILE = path_to_data_dir('library_tag_cache')
        settings.LOCAL_MUSIC_PATH = path_to_data_dir('')

        super(LocalLibraryControllerTest, self).setUp()

    def tearDown(self):
        settings.runtime.clear()

        super(LocalLibraryControllerTest, self).tearDown()
