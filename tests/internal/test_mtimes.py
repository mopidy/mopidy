import os
import pathlib
import shutil

import pytest

from mopidy import exceptions
from mopidy.internal import mtimes

import tests


@pytest.fixture
def tmp_dir_path(tmp_path):
    yield tmp_path
    if tmp_path.is_dir():
        shutil.rmtree(str(tmp_path))


def test_names_are_pathlib_objects():
    result, errors = mtimes.find_mtimes(str(tests.path_to_data_dir("")))

    for name in list(result.keys()) + list(errors.keys()):
        assert isinstance(name, pathlib.Path)


def test_nonexistent_dir_is_an_error(tmp_dir_path):
    missing_path = tmp_dir_path / "does-not-exist"

    result, errors = mtimes.find_mtimes(missing_path)

    assert result == {}
    assert errors == {missing_path: tests.IsA(exceptions.FindError)}


def test_empty_dirs_are_not_in_the_result(tmp_dir_path):
    """Empty directories should not show up in results"""
    dir_path = tmp_dir_path / "empty"
    dir_path.mkdir()

    result, errors = mtimes.find_mtimes(dir_path)

    assert result == {}
    assert errors == {}


def test_file_as_the_root_just_returns_the_file(tmp_dir_path):
    file_path = tmp_dir_path / "single"
    file_path.touch()

    result, errors = mtimes.find_mtimes(file_path)

    assert result == {file_path: tests.any_int}
    assert errors == {}


def test_nested_directories(tmp_dir_path):
    # Setup foo/bar and baz directories
    foo_path = tmp_dir_path / "foo" / "file"
    foo_path.parent.mkdir()
    foo_path.touch()
    foo_bar_path = tmp_dir_path / "foo" / "bar" / "filee"
    foo_bar_path.parent.mkdir()
    foo_bar_path.touch()
    baz_path = tmp_dir_path / "baz" / "file"
    baz_path.parent.mkdir()
    baz_path.touch()

    result, errors = mtimes.find_mtimes(tmp_dir_path)

    assert result == {
        foo_path: tests.any_int,
        foo_bar_path: tests.any_int,
        baz_path: tests.any_int,
    }
    assert errors == {}


def test_missing_permission_to_file_is_not_an_error(tmp_dir_path):
    """Missing permissions to a file is not a search error"""
    file_path = tmp_dir_path / "file"
    file_path.touch(mode=0o000)

    result, errors = mtimes.find_mtimes(tmp_dir_path)

    assert result == {file_path: tests.any_int}
    assert errors == {}

    file_path.chmod(0o644)


def test_missing_permission_to_directory_is_an_error(tmp_dir_path):
    dir_path = tmp_dir_path / "dir"
    dir_path.mkdir(mode=0o000)

    result, errors = mtimes.find_mtimes(tmp_dir_path)

    assert result == {}
    assert errors == {dir_path: tests.IsA(exceptions.FindError)}

    dir_path.chmod(0o755)


def test_symlinks_are_by_default_an_error(tmp_dir_path):
    """By default symlinks should be treated as an error"""
    file_path = tmp_dir_path / "file"
    file_path.touch()
    link_path = tmp_dir_path / "link"
    link_path.symlink_to(file_path)

    result, errors = mtimes.find_mtimes(tmp_dir_path)

    assert result == {file_path: tests.any_int}
    assert errors == {link_path: tests.IsA(exceptions.FindError)}


def test_with_follow_symlink_to_file_as_root_is_followed(tmp_dir_path):
    file_path = tmp_dir_path / "file"
    file_path.touch()
    link_path = tmp_dir_path / "link"
    link_path.symlink_to(file_path)

    result, errors = mtimes.find_mtimes(link_path, follow=True)

    assert result == {file_path: tests.any_int}
    assert errors == {}


def test_symlink_to_directory_is_followed(tmp_dir_path):
    file_path = tmp_dir_path / "dir" / "file"
    file_path.parent.mkdir()
    file_path.touch()
    link_path = tmp_dir_path / "link"
    link_path.symlink_to(file_path.parent, target_is_directory=True)

    result, errors = mtimes.find_mtimes(link_path, follow=True)

    assert result == {file_path: tests.any_int}
    assert errors == {}


def test_symlink_pointing_at_itself_fails(tmp_dir_path):
    link_path = tmp_dir_path / "link"
    link_path.symlink_to(link_path)

    result, errors = mtimes.find_mtimes(tmp_dir_path, follow=True)

    assert result == {}
    assert errors == {link_path: tests.IsA(exceptions.FindError)}


def test_symlink_pointing_at_parent_fails(tmp_dir_path):
    """We should detect a loop via the parent and give up on the branch"""

    link_path = tmp_dir_path / "link"
    link_path.symlink_to(tmp_dir_path, target_is_directory=True)

    result, errors = mtimes.find_mtimes(tmp_dir_path, follow=True)

    assert result == {}
    assert errors == {link_path: tests.IsA(Exception)}


def test_indirect_symlink_loop(tmp_dir_path):
    """More indirect loops should also be detected"""
    # Setup tmpdir/directory/loop where loop points to tmpdir
    link_path = tmp_dir_path / "dir" / "link"
    link_path.parent.mkdir()
    link_path.symlink_to(tmp_dir_path, target_is_directory=True)

    result, errors = mtimes.find_mtimes(tmp_dir_path, follow=True)

    assert result == {}
    assert errors == {link_path: tests.IsA(Exception)}


def test_symlink_branches_are_not_excluded(tmp_dir_path):
    """Using symlinks to make a file show up multiple times should work"""
    file_path = tmp_dir_path / "dir" / "file"
    file_path.parent.mkdir()
    file_path.touch()
    link1_path = tmp_dir_path / "link1"
    link1_path.symlink_to(file_path)
    link2_path = tmp_dir_path / "link2"
    link2_path.symlink_to(file_path)

    result, errors = mtimes.find_mtimes(tmp_dir_path, follow=True)

    assert result == {
        file_path: tests.any_int,
        link1_path: tests.any_int,
        link2_path: tests.any_int,
    }
    assert errors == {}


def test_gives_mtime_in_milliseconds(tmp_dir_path):
    file_path = tmp_dir_path / "file"
    file_path.touch()

    os.utime(str(file_path), (1, 3.14159265))

    result, errors = mtimes.find_mtimes(tmp_dir_path)

    assert result == {file_path: 3141}
    assert errors == {}
