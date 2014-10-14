# encoding: utf-8

from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

import glib

from mopidy.utils import path

import tests


class GetOrCreateDirTest(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.parent):
            shutil.rmtree(self.parent)

    def test_creating_dir(self):
        dir_path = os.path.join(self.parent, b'test')
        self.assert_(not os.path.exists(dir_path))
        created = path.get_or_create_dir(dir_path)
        self.assert_(os.path.exists(dir_path))
        self.assert_(os.path.isdir(dir_path))
        self.assertEqual(created, dir_path)

    def test_creating_nested_dirs(self):
        level2_dir = os.path.join(self.parent, b'test')
        level3_dir = os.path.join(self.parent, b'test', b'test')
        self.assert_(not os.path.exists(level2_dir))
        self.assert_(not os.path.exists(level3_dir))
        created = path.get_or_create_dir(level3_dir)
        self.assert_(os.path.exists(level2_dir))
        self.assert_(os.path.isdir(level2_dir))
        self.assert_(os.path.exists(level3_dir))
        self.assert_(os.path.isdir(level3_dir))
        self.assertEqual(created, level3_dir)

    def test_creating_existing_dir(self):
        created = path.get_or_create_dir(self.parent)
        self.assert_(os.path.exists(self.parent))
        self.assert_(os.path.isdir(self.parent))
        self.assertEqual(created, self.parent)

    def test_create_dir_with_name_of_existing_file_throws_oserror(self):
        conflicting_file = os.path.join(self.parent, b'test')
        open(conflicting_file, 'w').close()
        dir_path = os.path.join(self.parent, b'test')
        with self.assertRaises(OSError):
            path.get_or_create_dir(dir_path)

    def test_create_dir_with_unicode(self):
        with self.assertRaises(ValueError):
            dir_path = unicode(os.path.join(self.parent, b'test'))
            path.get_or_create_dir(dir_path)

    def test_create_dir_with_none(self):
        with self.assertRaises(ValueError):
            path.get_or_create_dir(None)


class GetOrCreateFileTest(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.parent):
            shutil.rmtree(self.parent)

    def test_creating_file(self):
        file_path = os.path.join(self.parent, b'test')
        self.assert_(not os.path.exists(file_path))
        created = path.get_or_create_file(file_path)
        self.assert_(os.path.exists(file_path))
        self.assert_(os.path.isfile(file_path))
        self.assertEqual(created, file_path)

    def test_creating_nested_file(self):
        level2_dir = os.path.join(self.parent, b'test')
        file_path = os.path.join(self.parent, b'test', b'test')
        self.assert_(not os.path.exists(level2_dir))
        self.assert_(not os.path.exists(file_path))
        created = path.get_or_create_file(file_path)
        self.assert_(os.path.exists(level2_dir))
        self.assert_(os.path.isdir(level2_dir))
        self.assert_(os.path.exists(file_path))
        self.assert_(os.path.isfile(file_path))
        self.assertEqual(created, file_path)

    def test_creating_existing_file(self):
        file_path = os.path.join(self.parent, b'test')
        path.get_or_create_file(file_path)
        created = path.get_or_create_file(file_path)
        self.assert_(os.path.exists(file_path))
        self.assert_(os.path.isfile(file_path))
        self.assertEqual(created, file_path)

    def test_create_file_with_name_of_existing_dir_throws_ioerror(self):
        conflicting_dir = os.path.join(self.parent)
        with self.assertRaises(IOError):
            path.get_or_create_file(conflicting_dir)

    def test_create_dir_with_unicode(self):
        with self.assertRaises(ValueError):
            file_path = unicode(os.path.join(self.parent, b'test'))
            path.get_or_create_file(file_path)

    def test_create_file_with_none(self):
        with self.assertRaises(ValueError):
            path.get_or_create_file(None)

    def test_create_dir_without_mkdir(self):
        file_path = os.path.join(self.parent, b'foo', b'bar')
        with self.assertRaises(IOError):
            path.get_or_create_file(file_path, mkdir=False)

    def test_create_dir_with_default_content(self):
        file_path = os.path.join(self.parent, b'test')
        created = path.get_or_create_file(file_path, content=b'foobar')
        with open(created) as fh:
            self.assertEqual(fh.read(), b'foobar')


class PathToFileURITest(unittest.TestCase):
    def test_simple_path(self):
        result = path.path_to_uri('/etc/fstab')
        self.assertEqual(result, 'file:///etc/fstab')

    def test_space_in_path(self):
        result = path.path_to_uri('/tmp/test this')
        self.assertEqual(result, 'file:///tmp/test%20this')

    def test_unicode_in_path(self):
        result = path.path_to_uri('/tmp/æøå')
        self.assertEqual(result, 'file:///tmp/%C3%A6%C3%B8%C3%A5')

    def test_utf8_in_path(self):
        result = path.path_to_uri('/tmp/æøå'.encode('utf-8'))
        self.assertEqual(result, 'file:///tmp/%C3%A6%C3%B8%C3%A5')

    def test_latin1_in_path(self):
        result = path.path_to_uri('/tmp/æøå'.encode('latin-1'))
        self.assertEqual(result, 'file:///tmp/%E6%F8%E5')


class UriToPathTest(unittest.TestCase):
    def test_simple_uri(self):
        result = path.uri_to_path('file:///etc/fstab')
        self.assertEqual(result, '/etc/fstab'.encode('utf-8'))

    def test_space_in_uri(self):
        result = path.uri_to_path('file:///tmp/test%20this')
        self.assertEqual(result, '/tmp/test this'.encode('utf-8'))

    def test_unicode_in_uri(self):
        result = path.uri_to_path('file:///tmp/%C3%A6%C3%B8%C3%A5')
        self.assertEqual(result, '/tmp/æøå'.encode('utf-8'))

    def test_latin1_in_uri(self):
        result = path.uri_to_path('file:///tmp/%E6%F8%E5')
        self.assertEqual(result, '/tmp/æøå'.encode('latin-1'))


class SplitPathTest(unittest.TestCase):
    def test_empty_path(self):
        self.assertEqual([], path.split_path(''))

    def test_single_dir(self):
        self.assertEqual(['foo'], path.split_path('foo'))

    def test_dirs(self):
        self.assertEqual(['foo', 'bar', 'baz'], path.split_path('foo/bar/baz'))

    def test_initial_slash_is_ignored(self):
        self.assertEqual(
            ['foo', 'bar', 'baz'], path.split_path('/foo/bar/baz'))

    def test_only_slash(self):
        self.assertEqual([], path.split_path('/'))


class ExpandPathTest(unittest.TestCase):
    # TODO: test via mocks?

    def test_empty_path(self):
        self.assertEqual(os.path.abspath(b'.'), path.expand_path(b''))

    def test_absolute_path(self):
        self.assertEqual(b'/tmp/foo', path.expand_path(b'/tmp/foo'))

    def test_home_dir_expansion(self):
        self.assertEqual(
            os.path.expanduser(b'~/foo'), path.expand_path(b'~/foo'))

    def test_abspath(self):
        self.assertEqual(os.path.abspath(b'./foo'), path.expand_path(b'./foo'))

    def test_xdg_subsititution(self):
        self.assertEqual(
            glib.get_user_data_dir() + b'/foo',
            path.expand_path(b'$XDG_DATA_DIR/foo'))

    def test_xdg_subsititution_unknown(self):
        self.assertIsNone(
            path.expand_path(b'/tmp/$XDG_INVALID_DIR/foo'))


class FindMTimesTest(unittest.TestCase):
    maxDiff = None

    # TODO: Consider if more of these directory structures should be created by
    # the test. This would make it more obvious what our expected result is.

    DOES_NOT_EXIST = tests.path_to_data_dir('does-no-exist')
    SINGLE_FILE = tests.path_to_data_dir('blank.mp3')
    SINGLE_SYMLINK = tests.path_to_data_dir('find2/bar')
    DATA_DIR = tests.path_to_data_dir('')
    FIND_DIR = tests.path_to_data_dir('find')
    FIND2_DIR = tests.path_to_data_dir('find2')
    NO_PERMISSION_DIR = tests.path_to_data_dir('no-permission')
    SYMLINK_LOOP = tests.path_to_data_dir('symlink-loop')

    def test_basic_dir(self):
        result, errors = path.find_mtimes(self.FIND_DIR)
        self.assert_(result)
        self.assertEqual(errors, {})

    def test_nonexistant_dir(self):
        result, errors = path.find_mtimes(self.DOES_NOT_EXIST)
        self.assertEqual(result, {})
        self.assertEqual(errors, {self.DOES_NOT_EXIST: tests.IsA(OSError)})

    def test_file(self):
        result, errors = path.find_mtimes(self.SINGLE_FILE)
        self.assertEqual(result, {self.SINGLE_FILE: tests.any_int})
        self.assertEqual(errors, {})

    def test_files(self):
        result, errors = path.find_mtimes(self.FIND_DIR)
        expected = {
            tests.path_to_data_dir(b'find/foo/bar/file'): tests.any_int,
            tests.path_to_data_dir(b'find/foo/file'): tests.any_int,
            tests.path_to_data_dir(b'find/baz/file'): tests.any_int}
        self.assertEqual(expected, result)
        self.assertEqual(errors, {})

    def test_names_are_bytestrings(self):
        for name in path.find_mtimes(self.DATA_DIR)[0]:
            self.assertEqual(name, tests.IsA(bytes))

    def test_symlinks_are_ignored(self):
        result, errors = path.find_mtimes(self.SINGLE_SYMLINK)
        self.assertEqual({}, result)
        self.assertEqual({self.SINGLE_SYMLINK: tests.IsA(Exception)}, errors)

    def test_missing_permission_to_file(self):
        # Note that we cannot know if we have access, but the stat will succeed
        with tempfile.NamedTemporaryFile() as tmp:
            os.chmod(tmp.name, 0)
            result, errors = path.find_mtimes(tmp.name)
            self.assertEqual({tmp.name: tests.any_int}, result)
            self.assertEqual({}, errors)

    def test_missing_permission_to_directory(self):
        result, errors = path.find_mtimes(self.NO_PERMISSION_DIR)
        self.assertEqual({}, result)
        self.assertEqual({self.NO_PERMISSION_DIR: tests.IsA(OSError)}, errors)

    def test_basic_symlink(self):
        result, errors = path.find_mtimes(self.SINGLE_SYMLINK, follow=True)
        self.assertEqual({self.SINGLE_SYMLINK: tests.any_int}, result)
        self.assertEqual({}, errors)

    def test_direct_symlink_loop(self):
        result, errors = path.find_mtimes(self.SYMLINK_LOOP, follow=True)
        self.assertEqual({}, result)
        self.assertEqual({self.SYMLINK_LOOP: tests.IsA(OSError)}, errors)


# TODO: kill this in favour of just os.path.getmtime + mocks
class MtimeTest(unittest.TestCase):
    def tearDown(self):
        path.mtime.undo_fake()

    def test_mtime_of_current_dir(self):
        mtime_dir = int(os.stat('.').st_mtime)
        self.assertEqual(mtime_dir, path.mtime('.'))

    def test_fake_time_is_returned(self):
        path.mtime.set_fake_time(123456)
        self.assertEqual(path.mtime('.'), 123456)
