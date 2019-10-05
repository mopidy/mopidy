# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import posixpath
import shutil
import sys
import tempfile
import unittest

import pytest

from mopidy import compat, exceptions, posix_normpath
from mopidy.internal import path
from mopidy.internal.gi import GLib

import tests


class GetOrCreateDirTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.parent = posix_normpath(tempfile.mkdtemp())

    def tearDown(self):  # noqa: N802
        if os.path.isdir(self.parent):
            shutil.rmtree(self.parent)

    def test_creating_dir(self):
        dir_path = posixpath.join(self.parent, b'test')
        self.assert_(not os.path.exists(dir_path))
        created = path.get_or_create_dir(dir_path)
        self.assert_(os.path.exists(dir_path))
        self.assert_(os.path.isdir(dir_path))
        self.assertEqual(created, dir_path)

    def test_creating_nested_dirs(self):
        level2_dir = posixpath.join(self.parent, b'test')
        level3_dir = posixpath.join(self.parent, b'test', b'test')
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
        conflicting_file = posixpath.join(self.parent, b'test')
        open(conflicting_file, 'w').close()
        dir_path = posixpath.join(self.parent, b'test')
        with self.assertRaises(OSError):
            path.get_or_create_dir(dir_path)

    def test_create_dir_with_unicode(self):
        with self.assertRaises(ValueError):
            dir_path = compat.text_type(posixpath.join(self.parent, b'test'))
            path.get_or_create_dir(dir_path)

    def test_create_dir_with_none(self):
        with self.assertRaises(ValueError):
            path.get_or_create_dir(None)


class GetOrCreateFileTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.parent = posix_normpath(tempfile.mkdtemp())

    def tearDown(self):  # noqa: N802
        if os.path.isdir(self.parent):
            shutil.rmtree(self.parent)

    def test_creating_file(self):
        file_path = posixpath.join(self.parent, b'test')
        self.assert_(not os.path.exists(file_path))
        created = path.get_or_create_file(file_path)
        self.assert_(os.path.exists(file_path))
        self.assert_(os.path.isfile(file_path))
        self.assertEqual(created, file_path)

    def test_creating_nested_file(self):
        level2_dir = posixpath.join(self.parent, b'test')
        file_path = posixpath.join(self.parent, b'test', b'test')
        self.assert_(not os.path.exists(level2_dir))
        self.assert_(not os.path.exists(file_path))
        created = path.get_or_create_file(file_path)
        self.assert_(os.path.exists(level2_dir))
        self.assert_(os.path.isdir(level2_dir))
        self.assert_(os.path.exists(file_path))
        self.assert_(os.path.isfile(file_path))
        self.assertEqual(created, file_path)

    def test_creating_existing_file(self):
        file_path = posixpath.join(self.parent, b'test')
        path.get_or_create_file(file_path)
        created = path.get_or_create_file(file_path)
        self.assert_(os.path.exists(file_path))
        self.assert_(os.path.isfile(file_path))
        self.assertEqual(created, file_path)

    def test_create_file_with_name_of_existing_dir_throws_ioerror(self):
        conflicting_dir = posixpath.join(self.parent)
        with self.assertRaises(IOError):
            path.get_or_create_file(conflicting_dir)

    def test_create_dir_with_unicode_filename_throws_value_error(self):
        with self.assertRaises(ValueError):
            file_path = compat.text_type(posixpath.join(self.parent, b'test'))
            path.get_or_create_file(file_path)

    def test_create_file_with_none_filename_throws_value_error(self):
        with self.assertRaises(ValueError):
            path.get_or_create_file(None)

    def test_create_dir_without_mkdir(self):
        file_path = posixpath.join(self.parent, b'foo', b'bar')
        with self.assertRaises(IOError):
            path.get_or_create_file(file_path, mkdir=False)

    def test_create_dir_with_bytes_content(self):
        file_path = posixpath.join(self.parent, b'test')
        created = path.get_or_create_file(file_path, content=b'foobar')
        with open(created) as fh:
            self.assertEqual(fh.read(), b'foobar')

    def test_create_dir_with_unicode_content(self):
        file_path = posixpath.join(self.parent, b'test')
        created = path.get_or_create_file(file_path, content='foobaræøå')
        with open(created) as fh:
            self.assertEqual(fh.read(), b'foobar\xc3\xa6\xc3\xb8\xc3\xa5')


class GetUnixSocketPathTest(unittest.TestCase):

    def test_correctly_matched_socket_path(self):
        self.assertEqual(
            path.get_unix_socket_path('unix:/tmp/mopidy.socket'),
            '/tmp/mopidy.socket'
        )

    def test_correctly_no_match_socket_path(self):
        self.assertIsNone(path.get_unix_socket_path('127.0.0.1'))


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
        self.assertEqual(posix_normpath(os.path.abspath(b'.')),
                         path.expand_path(b''))

    @unittest.skipIf(sys.platform == 'win32',
                     'win32 absolute paths include drive')
    def test_absolute_path(self):
        self.assertEqual(b'/tmp/foo', path.expand_path(b'/tmp/foo'))

    @unittest.skipUnless(sys.platform == 'win32',
                         'win32 absolute paths include drive')
    def test_absolute_path_win32(self):
        self.assertEqual(b'k:/tmp/foo', path.expand_path(b'k:/tmp/foo'))

    def test_home_dir_expansion(self):
        self.assertEqual(
            posix_normpath(os.path.expanduser(b'~/foo')),
            path.expand_path(b'~/foo'))

    def test_abspath(self):
        self.assertEqual(posix_normpath(os.path.abspath(b'./foo')),
                         path.expand_path(b'./foo'))

    @unittest.skipIf(sys.platform == 'win32',
                     reason="don't understand this yet")
#   in win32, get_user_data_dir provides '~/HOME/AppData/Local/foo'
#       and XDG_DATA_DIR expansion provided '~/HOME/.local/share/foo'
#   which is correct?
    def test_xdg_substitution(self):
        self.assertEqual(
            posix_normpath(GLib.get_user_data_dir()) + b'/foo',
            path.expand_path(b'$XDG_DATA_DIR/foo'))

    def test_xdg_substitution_unknown(self):
        self.assertIsNone(
            path.expand_path(b'/tmp/$XDG_INVALID_DIR/foo'))


class FindMTimesTest(unittest.TestCase):
    maxDiff = None  # noqa: N815

    def setUp(self):  # noqa: N802
        self.tmpdir = posix_normpath(tempfile.mkdtemp(b'.mopidy-tests'))
        # self.tmpdir = tempfile.mkdtemp(b'.mopidy-tests')

    def tearDown(self):  # noqa: N802
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def mkdir(self, *args):
        name = posix_normpath(self.tmpdir, *[bytes(a) for a in args])
        os.mkdir(name)
        return name

    def touch(self, *args):
        name = posix_normpath(self.tmpdir, *[bytes(a) for a in args])
        open(name, 'w').close()
        return name

    def test_names_are_bytestrings(self):
        """We shouldn't be mixing in unicode for paths."""
        result, errors = path.find_mtimes(tests.path_to_data_dir(''))
        for name in result.keys() + errors.keys():
            self.assertEqual(name, tests.IsA(bytes))

    def test_nonexistent_dir(self):
        """Non existent search roots are an error"""
        missing = posixpath.join(self.tmpdir, 'does-not-exist')
        result, errors = path.find_mtimes(missing)
        self.assertEqual(result, {})
        self.assertEqual(errors, {missing: tests.IsA(exceptions.FindError)})

    def test_empty_dir(self):
        """Empty directories should not show up in results"""
        self.mkdir('empty')

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual(result, {})
        self.assertEqual(errors, {})

    def test_file_as_the_root(self):
        """Specifying a file as the root should just return the file"""
        single = self.touch('single')

        result, errors = path.find_mtimes(single)
        self.assertEqual(result, {single: tests.any_int})
        self.assertEqual(errors, {})

    def test_nested_directories(self):
        """Searching nested directories should find all files"""

        # Setup foo/bar and baz directories
        self.mkdir('foo')
        self.mkdir('foo', 'bar')
        self.mkdir('baz')

        # Touch foo/file foo/bar/file and baz/file
        foo_file = self.touch('foo', 'file')
        foo_bar_file = self.touch('foo', 'bar', 'file')
        baz_file = self.touch('baz', 'file')

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual(result, {foo_file: tests.any_int,
                                  foo_bar_file: tests.any_int,
                                  baz_file: tests.any_int})
        self.assertEqual(errors, {})

    def test_missing_permission_to_file(self):
        """Missing permissions to a file is not a search error"""
        target = self.touch('no-permission')
        os.chmod(target, 0)

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual({target: tests.any_int}, result)
        self.assertEqual({}, errors)

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="chmod on win32 only sets read-permission")
    def test_missing_permission_to_directory(self):
        """Missing permissions to a directory is an error"""
        directory = self.mkdir('no-permission')
        os.chmod(directory, 0)

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual({}, result)
        self.assertEqual({directory: tests.IsA(exceptions.FindError)}, errors)

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="symlinks not supported by 2.7 os module")
    def test_symlinks_are_ignored(self):
        """By default symlinks should be treated as an error"""
        target = self.touch('target')
        link = posixpath.join(self.tmpdir, 'link')
        os.symlink(target, link)

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual(result, {target: tests.any_int})
        self.assertEqual(errors, {link: tests.IsA(exceptions.FindError)})

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="symlinks not supported by 2.7 os module")
    def test_symlink_to_file_as_root_is_followed(self):
        """Passing a symlink as the root should be followed when follow=True"""
        target = self.touch('target')
        link = posixpath.join(self.tmpdir, 'link')
        os.symlink(target, link)

        result, errors = path.find_mtimes(link, follow=True)
        self.assertEqual({link: tests.any_int}, result)
        self.assertEqual({}, errors)

    def test_symlink_to_directory_is_followed(self):
        pass

    @unittest.skipIf(sys.platform == 'win32',
                     reason="symlinks not supported by 2.7 os module")
    def test_symlink_pointing_at_itself_fails(self):
        """Symlink pointing at itself should give as an OS error"""
        link = posixpath.join(self.tmpdir, 'link')
        os.symlink(link, link)

        result, errors = path.find_mtimes(link, follow=True)
        self.assertEqual({}, result)
        self.assertEqual({link: tests.IsA(exceptions.FindError)}, errors)

    @unittest.skipIf(sys.platform == 'win32',
                     reason="symlinks not supported by 2.7 os module")
    def test_symlink_pointing_at_parent_fails(self):
        """We should detect a loop via the parent and give up on the branch"""
        os.symlink(self.tmpdir, posixpath.join(self.tmpdir, 'link'))

        result, errors = path.find_mtimes(self.tmpdir, follow=True)
        self.assertEqual({}, result)
        self.assertEqual(1, len(errors))
        self.assertEqual(tests.IsA(Exception), errors.values()[0])

    @unittest.skipIf(sys.platform == 'win32',
                     reason="symlinks not supported by 2.7 os module")
    def test_indirect_symlink_loop(self):
        """More indirect loops should also be detected"""
        # Setup tmpdir/directory/loop where loop points to tmpdir
        directory = posixpath.join(self.tmpdir, b'directory')
        loop = posixpath.join(directory, b'loop')

        os.mkdir(directory)
        os.symlink(self.tmpdir, loop)

        result, errors = path.find_mtimes(self.tmpdir, follow=True)
        self.assertEqual({}, result)
        self.assertEqual({loop: tests.IsA(Exception)}, errors)

    @unittest.skipIf(sys.platform == 'win32',
                     reason="symlinks not supported by 2.7 os module")
    def test_symlink_branches_are_not_excluded(self):
        """Using symlinks to make a file show up multiple times should work"""
        self.mkdir('directory')
        target = self.touch('directory', 'target')
        link1 = posixpath.join(self.tmpdir, b'link1')
        link2 = posixpath.join(self.tmpdir, b'link2')

        os.symlink(target, link1)
        os.symlink(target, link2)

        expected = {target: tests.any_int,
                    link1: tests.any_int,
                    link2: tests.any_int}

        result, errors = path.find_mtimes(self.tmpdir, follow=True)
        self.assertEqual(expected, result)
        self.assertEqual({}, errors)

    def test_gives_mtime_in_milliseconds(self):
        fname = self.touch('foobar')

        os.utime(fname, (1, 3.14159265))

        result, errors = path.find_mtimes(fname)

        self.assertEqual(len(result), 1)
        mtime, = result.values()
        self.assertEqual(mtime, 3141)
        self.assertEqual(errors, {})


class TestIsPathInsideBaseDir(object):
    def test_when_inside(self):
        assert path.is_path_inside_base_dir(
            '/æ/øå'.encode('utf-8'),
            '/æ'.encode('utf-8'))

    def test_when_outside(self):
        assert not path.is_path_inside_base_dir(
            '/æ/øå'.encode('utf-8'),
            '/ø'.encode('utf-8'))

    def test_byte_inside_str_fails(self):
        with pytest.raises(ValueError):
            path.is_path_inside_base_dir('/æ/øå'.encode('utf-8'), '/æ')

    def test_str_inside_byte_fails(self):
        with pytest.raises(ValueError):
            path.is_path_inside_base_dir('/æ/øå', '/æ'.encode('utf-8'))

    def test_str_inside_str_fails(self):
        with pytest.raises(ValueError):
            path.is_path_inside_base_dir('/æ/øå', '/æ')


# TODO: kill this in favour of just os.path.getmtime + mocks
class MtimeTest(unittest.TestCase):

    def tearDown(self):  # noqa: N802
        path.mtime.undo_fake()

    def test_mtime_of_current_dir(self):
        mtime_dir = int(os.stat('.').st_mtime)
        self.assertEqual(mtime_dir, path.mtime('.'))

    def test_fake_time_is_returned(self):
        path.mtime.set_fake_time(123456)
        self.assertEqual(path.mtime('.'), 123456)
