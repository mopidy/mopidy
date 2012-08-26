# encoding: utf-8

import os
import shutil
import sys
import tempfile

from mopidy.utils.path import (get_or_create_folder, mtime,
    path_to_uri, uri_to_path, split_path, find_files)

from tests import unittest, path_to_data_dir


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

    def test_creating_nested_folders(self):
        level2_folder = os.path.join(self.parent, 'test')
        level3_folder = os.path.join(self.parent, 'test', 'test')
        self.assert_(not os.path.exists(level2_folder))
        self.assert_(not os.path.isdir(level2_folder))
        self.assert_(not os.path.exists(level3_folder))
        self.assert_(not os.path.isdir(level3_folder))
        created = get_or_create_folder(level3_folder)
        self.assert_(os.path.exists(level2_folder))
        self.assert_(os.path.isdir(level2_folder))
        self.assert_(os.path.exists(level3_folder))
        self.assert_(os.path.isdir(level3_folder))
        self.assertEqual(created, level3_folder)

    def test_creating_existing_folder(self):
        created = get_or_create_folder(self.parent)
        self.assert_(os.path.exists(self.parent))
        self.assert_(os.path.isdir(self.parent))
        self.assertEqual(created, self.parent)

    def test_create_folder_with_name_of_existing_file_throws_oserror(self):
        conflicting_file = os.path.join(self.parent, 'test')
        open(conflicting_file, 'w').close()
        folder = os.path.join(self.parent, 'test')
        self.assertRaises(OSError, get_or_create_folder, folder)


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


class UriToPathTest(unittest.TestCase):
    def test_simple_uri(self):
        if sys.platform == 'win32':
            result = uri_to_path('file:///C://WINDOWS/clock.avi')
            self.assertEqual(result, u'C:/WINDOWS/clock.avi')
        else:
            result = uri_to_path('file:///etc/fstab')
            self.assertEqual(result, u'/etc/fstab')

    def test_space_in_uri(self):
        if sys.platform == 'win32':
            result = uri_to_path('file:///C://test%20this')
            self.assertEqual(result, u'C:/test this')
        else:
            result = uri_to_path(u'file:///tmp/test%20this')
            self.assertEqual(result, u'/tmp/test this')

    def test_unicode_in_uri(self):
        if sys.platform == 'win32':
            result = uri_to_path( 'file:///C://%C3%A6%C3%B8%C3%A5')
            self.assertEqual(result, u'C:/æøå')
        else:
            result = uri_to_path(u'file:///tmp/%C3%A6%C3%B8%C3%A5')
            self.assertEqual(result, u'/tmp/æøå')


class SplitPathTest(unittest.TestCase):
    def test_empty_path(self):
        self.assertEqual([], split_path(''))

    def test_single_folder(self):
        self.assertEqual(['foo'], split_path('foo'))

    def test_folders(self):
        self.assertEqual(['foo', 'bar', 'baz'], split_path('foo/bar/baz'))

    def test_folders(self):
        self.assertEqual(['foo', 'bar', 'baz'], split_path('foo/bar/baz'))

    def test_initial_slash_is_ignored(self):
        self.assertEqual(['foo', 'bar', 'baz'], split_path('/foo/bar/baz'))

    def test_only_slash(self):
        self.assertEqual([], split_path('/'))


class FindFilesTest(unittest.TestCase):
    def find(self, path):
        return list(find_files(path_to_data_dir(path)))

    def test_basic_folder(self):
        self.assert_(self.find(''))

    def test_nonexistant_folder(self):
        self.assertEqual(self.find('does-not-exist'), [])

    def test_file(self):
        files = self.find('blank.mp3')
        self.assertEqual(len(files), 1)
        self.assert_(files[0], path_to_data_dir('blank.mp3'))

    def test_names_are_unicode(self):
        is_unicode = lambda f: isinstance(f, unicode)
        for name in self.find(''):
            self.assert_(is_unicode(name),
                '%s is not unicode object' % repr(name))


class MtimeTest(unittest.TestCase):
    def tearDown(self):
        mtime.undo_fake()

    def test_mtime_of_current_dir(self):
        mtime_dir = int(os.stat('.').st_mtime)
        self.assertEqual(mtime_dir, mtime('.'))

    def test_fake_time_is_returned(self):
        mtime.set_fake_time(123456)
        self.assertEqual(mtime('.'), 123456)
