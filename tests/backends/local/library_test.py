import unittest

# FIXME Our Windows build server does not support GStreamer yet
import sys
if sys.platform == 'win32':
    from tests import SkipTest
    raise SkipTest

from mopidy import settings
from mopidy.backends.local import LocalBackend

from tests import data_folder
from tests.backends.base.library import BaseLibraryControllerTest

class LocalLibraryControllerTest(BaseLibraryControllerTest, unittest.TestCase):

    backend_class = LocalBackend

    def setUp(self):
        settings.LOCAL_TAG_CACHE = data_folder('library_tag_cache')
        settings.LOCAL_MUSIC_FOLDER = data_folder('')

        super(LocalLibraryControllerTest, self).setUp()

    def tearDown(self):
        settings.runtime.clear()

        super(LocalLibraryControllerTest, self).tearDown()
