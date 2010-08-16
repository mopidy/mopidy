# encoding: utf-8

import os
import shutil
import sys
import tempfile
import unittest

from mopidy.utils.path import get_or_create_folder, path_to_uri

from tests import SkipTest

class GetOrCreateFolderTest(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.parent):
            shutil.rmtree(self.parent)

    def test_creating_folder(self):
        folder = os.path.join(self.parent, 'test')
        self.assert_(not os.path.exists(folder))
        self.assert_(not os.path.isdir(folder))
        created = get_or_create_folder(folder)
        self.assert_(os.path.exists(folder))
        self.assert_(os.path.isdir(folder))
        self.assertEqual(created, folder)

    def test_creating_existing_folder(self):
        created = get_or_create_folder(self.parent)
        self.assert_(os.path.exists(self.parent))
        self.assert_(os.path.isdir(self.parent))
        self.assertEqual(created, self.parent)

    def test_that_userfolder_is_expanded(self):
        raise SkipTest # Not sure how to safely test this


class PathToFileURITest(unittest.TestCase):
    def test_simple_path(self):
        if sys.platform == 'win32':
            result = path_to_uri(u'C:/WINDOWS/clock.avi')
            self.assertEqual(result, 'file:///C://WINDOWS/clock.avi')
        else:
            result = path_to_uri(u'/etc/fstab')
            self.assertEqual(result, 'file:///etc/fstab')

    def test_folder_and_path(self):
        if sys.platform == 'win32':
            result = path_to_uri(u'C:/WINDOWS/', u'clock.avi')
            self.assertEqual(result, 'file:///C://WINDOWS/clock.avi')
        else:
            result = path_to_uri(u'/etc', u'fstab')
            self.assertEqual(result, u'file:///etc/fstab')

    def test_space_in_path(self):
        if sys.platform == 'win32':
            result = path_to_uri(u'C:/test this')
            self.assertEqual(result, 'file:///C://test%20this')
        else:
            result = path_to_uri(u'/tmp/test this')
            self.assertEqual(result, u'file:///tmp/test%20this')

    def test_unicode_in_path(self):
        if sys.platform == 'win32':
            result = path_to_uri(u'C:/æøå')
            self.assertEqual(result, 'file:///C://%C3%A6%C3%B8%C3%A5')
        else:
            result = path_to_uri(u'/tmp/æøå')
            self.assertEqual(result, u'file:///tmp/%C3%A6%C3%B8%C3%A5')
