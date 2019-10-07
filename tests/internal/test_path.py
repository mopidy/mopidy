# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import shutil
import tempfile
import unittest

import pytest

from mopidy import compat, exceptions
from mopidy.compat import pathlib
from mopidy.internal import path
from mopidy.internal.gi import GLib

import tests


class GetOrCreateDirTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.parent = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):  # noqa: N802
        if self.parent.is_dir():
            shutil.rmtree(str(self.parent))

    def test_creating_dir(self):
        dir_path = self.parent / 'test'
        assert not dir_path.exists()

        created = path.get_or_create_dir(str(dir_path))

        assert dir_path.is_dir()
        assert created == dir_path

    def test_creating_nested_dirs(self):
        level2_dir = self.parent / 'test'
        level3_dir = self.parent / 'test' / 'test'
        assert not level2_dir.exists()
        assert not level3_dir.exists()

        created = path.get_or_create_dir(str(level3_dir))

        assert level2_dir.is_dir()
        assert level3_dir.is_dir()
        assert created == level3_dir

    def test_creating_existing_dir(self):
        created = path.get_or_create_dir(str(self.parent))

        assert self.parent.is_dir()
        assert created == self.parent

    def test_create_dir_with_name_of_existing_file_throws_oserror(self):
        conflicting_file = self.parent / 'test'
        conflicting_file.touch()
        dir_path = self.parent / 'test'

        with pytest.raises(OSError):
            path.get_or_create_dir(str(dir_path))

    def test_create_dir_with_none(self):
        with pytest.raises(TypeError):
            path.get_or_create_dir(None)


class GetOrCreateFileTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.parent = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):  # noqa: N802
        if self.parent.is_dir():
            shutil.rmtree(str(self.parent))

    def test_creating_file(self):
        file_path = self.parent / 'test'
        assert not file_path.exists()

        created = path.get_or_create_file(str(file_path))

        assert file_path.is_file()
        assert created == file_path

    def test_creating_nested_file(self):
        level2_dir = self.parent / 'test'
        file_path = self.parent / 'test' / 'test'
        assert not level2_dir.exists()
        assert not file_path.exists()

        created = path.get_or_create_file(str(file_path))

        assert level2_dir.is_dir()
        assert file_path.is_file()
        assert created == file_path

    def test_creating_existing_file(self):
        file_path = self.parent / 'test'
        path.get_or_create_file(str(file_path))

        created = path.get_or_create_file(str(file_path))

        assert file_path.is_file()
        assert created == file_path

    def test_create_file_with_name_of_existing_dir_throws_error(self):
        with pytest.raises(OSError):
            path.get_or_create_file(self.parent)

    def test_create_file_with_none_filename_throws_type_error(self):
        with pytest.raises(TypeError):
            path.get_or_create_file(None)

    def test_create_dir_without_mkdir(self):
        file_path = self.parent / 'foo' / 'bar'

        with pytest.raises(OSError):
            path.get_or_create_file(file_path, mkdir=False)

    def test_create_dir_with_bytes_content(self):
        file_path = self.parent / 'test'

        created = path.get_or_create_file(str(file_path), content=b'foobar')

        assert created.read_bytes() == b'foobar'

    def test_create_dir_with_unicode_content(self):
        file_path = self.parent / 'test'

        created = path.get_or_create_file(str(file_path), content='foobaræøå')
        assert created.read_bytes() == b'foobar\xc3\xa6\xc3\xb8\xc3\xa5'


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

        assert result == 'file:///etc/fstab'

    def test_space_in_path(self):
        result = path.path_to_uri('/tmp/test this')

        assert result == 'file:///tmp/test%20this'

    def test_unicode_in_path(self):
        result = path.path_to_uri('/tmp/æøå')

        assert result == 'file:///tmp/%C3%A6%C3%B8%C3%A5'


class UriToPathTest(unittest.TestCase):

    def test_simple_uri(self):
        result = path.uri_to_path('file:///etc/fstab')

        assert result == pathlib.Path('/etc/fstab')

    def test_space_in_uri(self):
        result = path.uri_to_path('file:///tmp/test%20this')

        assert result == pathlib.Path('/tmp/test this')

    def test_unicode_in_uri(self):
        result = path.uri_to_path('file:///tmp/%C3%A6%C3%B8%C3%A5')

        assert result == pathlib.Path('/tmp/æøå')

    def test_latin1_in_uri(self):
        result = path.uri_to_path('file:///tmp/%E6%F8%E5')

        assert bytes(result) == b'/tmp/\xe6\xf8\xe5'


class ExpandPathTest(unittest.TestCase):
    def test_empty_path(self):
        result = path.expand_path('')

        assert result == pathlib.Path('.').resolve()

    def test_absolute_path(self):
        result = path.expand_path('/tmp/foo')

        assert result == pathlib.Path('/tmp/foo')

    def test_home_dir_expansion(self):
        result = path.expand_path('~/foo')

        assert result == pathlib.Path('~/foo').expanduser()

    def test_abspath(self):
        result = path.expand_path('./foo')

        assert result == pathlib.Path('./foo').resolve()

    def test_xdg_subsititution(self):
        expected = GLib.get_user_data_dir() + '/foo'
        result = path.expand_path('$XDG_DATA_DIR/foo')

        assert str(result) == expected

    def test_xdg_subsititution_unknown(self):
        result = path.expand_path('/tmp/$XDG_INVALID_DIR/foo')

        assert result is None


class FindMTimesTest(unittest.TestCase):
    maxDiff = None  # noqa: N815

    def setUp(self):  # noqa: N802
        self.tmpdir = tempfile.mkdtemp('.mopidy-tests').encode('utf-8')

    def tearDown(self):  # noqa: N802
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def mkdir(self, *args):
        name = os.path.join(self.tmpdir, *[a.encode('utf-8') for a in args])
        os.mkdir(name)
        return name

    def touch(self, *args):
        name = os.path.join(self.tmpdir, *[a.encode('utf-8') for a in args])
        open(name, 'w').close()
        return name

    def test_names_are_bytestrings(self):
        """We shouldn't be mixing in unicode for paths."""
        result, errors = path.find_mtimes(tests.path_to_data_dir(''))
        for name in list(result.keys()) + list(errors.keys()):
            self.assertEqual(name, tests.IsA(bytes))

    def test_nonexistent_dir(self):
        """Non existent search roots are an error"""
        missing = os.path.join(self.tmpdir, b'does-not-exist')
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

    def test_missing_permission_to_directory(self):
        """Missing permissions to a directory is an error"""
        directory = self.mkdir('no-permission')
        os.chmod(directory, 0)

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual({}, result)
        self.assertEqual({directory: tests.IsA(exceptions.FindError)}, errors)

    def test_symlinks_are_ignored(self):
        """By default symlinks should be treated as an error"""
        target = self.touch('target')
        link = os.path.join(self.tmpdir, b'link')
        os.symlink(target, link)

        result, errors = path.find_mtimes(self.tmpdir)
        self.assertEqual(result, {target: tests.any_int})
        self.assertEqual(errors, {link: tests.IsA(exceptions.FindError)})

    def test_symlink_to_file_as_root_is_followed(self):
        """Passing a symlink as the root should be followed when follow=True"""
        target = self.touch('target')
        link = os.path.join(self.tmpdir, b'link')
        os.symlink(target, link)

        result, errors = path.find_mtimes(link, follow=True)
        self.assertEqual({link: tests.any_int}, result)
        self.assertEqual({}, errors)

    def test_symlink_to_directory_is_followed(self):
        pass

    def test_symlink_pointing_at_itself_fails(self):
        """Symlink pointing at itself should give as an OS error"""
        link = os.path.join(self.tmpdir, b'link')
        os.symlink(link, link)

        result, errors = path.find_mtimes(link, follow=True)
        self.assertEqual({}, result)
        self.assertEqual({link: tests.IsA(exceptions.FindError)}, errors)

    def test_symlink_pointing_at_parent_fails(self):
        """We should detect a loop via the parent and give up on the branch"""
        os.symlink(self.tmpdir, os.path.join(self.tmpdir, b'link'))

        result, errors = path.find_mtimes(self.tmpdir, follow=True)
        self.assertEqual({}, result)
        self.assertEqual(1, len(errors))
        self.assertEqual(tests.IsA(Exception), list(errors.values())[0])

    def test_indirect_symlink_loop(self):
        """More indirect loops should also be detected"""
        # Setup tmpdir/directory/loop where loop points to tmpdir
        directory = os.path.join(self.tmpdir, b'directory')
        loop = os.path.join(directory, b'loop')

        os.mkdir(directory)
        os.symlink(self.tmpdir, loop)

        result, errors = path.find_mtimes(self.tmpdir, follow=True)
        self.assertEqual({}, result)
        self.assertEqual({loop: tests.IsA(Exception)}, errors)

    def test_symlink_branches_are_not_excluded(self):
        """Using symlinks to make a file show up multiple times should work"""
        self.mkdir('directory')
        target = self.touch('directory', 'target')
        link1 = os.path.join(self.tmpdir, b'link1')
        link2 = os.path.join(self.tmpdir, b'link2')

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
        with pytest.raises(TypeError):
            path.is_path_inside_base_dir('/æ/øå'.encode('utf-8'), '/æ')

    def test_str_inside_byte_fails(self):
        with pytest.raises(TypeError):
            path.is_path_inside_base_dir('/æ/øå', '/æ'.encode('utf-8'))

    def test_str_inside_str_fails(self):
        with pytest.raises(TypeError):
            path.is_path_inside_base_dir('/æ/øå', '/æ')
