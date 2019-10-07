import os
import shutil
import tempfile
import unittest

from mopidy import exceptions
from mopidy.internal import mtimes

import tests


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

    def test_names_are_native_strings(self):
        """We shouldn't be mixing in unicode for paths."""
        result, errors = mtimes.find_mtimes(str(tests.path_to_data_dir('')))
        for name in list(result.keys()) + list(errors.keys()):
            self.assertEqual(name, tests.IsA(str))

    def test_nonexistent_dir(self):
        """Non existent search roots are an error"""
        missing = os.path.join(self.tmpdir, b'does-not-exist')
        result, errors = mtimes.find_mtimes(missing)
        self.assertEqual(result, {})
        self.assertEqual(errors, {missing: tests.IsA(exceptions.FindError)})

    def test_empty_dir(self):
        """Empty directories should not show up in results"""
        self.mkdir('empty')

        result, errors = mtimes.find_mtimes(self.tmpdir)
        self.assertEqual(result, {})
        self.assertEqual(errors, {})

    def test_file_as_the_root(self):
        """Specifying a file as the root should just return the file"""
        single = self.touch('single')

        result, errors = mtimes.find_mtimes(single)
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

        result, errors = mtimes.find_mtimes(self.tmpdir)
        self.assertEqual(result, {foo_file: tests.any_int,
                                  foo_bar_file: tests.any_int,
                                  baz_file: tests.any_int})
        self.assertEqual(errors, {})

    def test_missing_permission_to_file(self):
        """Missing permissions to a file is not a search error"""
        target = self.touch('no-permission')
        os.chmod(target, 0)

        result, errors = mtimes.find_mtimes(self.tmpdir)
        self.assertEqual({target: tests.any_int}, result)
        self.assertEqual({}, errors)

    def test_missing_permission_to_directory(self):
        """Missing permissions to a directory is an error"""
        directory = self.mkdir('no-permission')
        os.chmod(directory, 0)

        result, errors = mtimes.find_mtimes(self.tmpdir)
        self.assertEqual({}, result)
        self.assertEqual({directory: tests.IsA(exceptions.FindError)}, errors)

    def test_symlinks_are_ignored(self):
        """By default symlinks should be treated as an error"""
        target = self.touch('target')
        link = os.path.join(self.tmpdir, b'link')
        os.symlink(target, link)

        result, errors = mtimes.find_mtimes(self.tmpdir)
        self.assertEqual(result, {target: tests.any_int})
        self.assertEqual(errors, {link: tests.IsA(exceptions.FindError)})

    def test_symlink_to_file_as_root_is_followed(self):
        """Passing a symlink as the root should be followed when follow=True"""
        target = self.touch('target')
        link = os.path.join(self.tmpdir, b'link')
        os.symlink(target, link)

        result, errors = mtimes.find_mtimes(link, follow=True)
        self.assertEqual({link: tests.any_int}, result)
        self.assertEqual({}, errors)

    def test_symlink_to_directory_is_followed(self):
        pass

    def test_symlink_pointing_at_itself_fails(self):
        """Symlink pointing at itself should give as an OS error"""
        link = os.path.join(self.tmpdir, b'link')
        os.symlink(link, link)

        result, errors = mtimes.find_mtimes(link, follow=True)
        self.assertEqual({}, result)
        self.assertEqual({link: tests.IsA(exceptions.FindError)}, errors)

    def test_symlink_pointing_at_parent_fails(self):
        """We should detect a loop via the parent and give up on the branch"""
        os.symlink(self.tmpdir, os.path.join(self.tmpdir, b'link'))

        result, errors = mtimes.find_mtimes(self.tmpdir, follow=True)
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

        result, errors = mtimes.find_mtimes(self.tmpdir, follow=True)
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

        result, errors = mtimes.find_mtimes(self.tmpdir, follow=True)
        self.assertEqual(expected, result)
        self.assertEqual({}, errors)

    def test_gives_mtime_in_milliseconds(self):
        fname = self.touch('foobar')

        os.utime(fname, (1, 3.14159265))

        result, errors = mtimes.find_mtimes(fname)

        self.assertEqual(len(result), 1)
        mtime, = result.values()
        self.assertEqual(mtime, 3141)
        self.assertEqual(errors, {})
