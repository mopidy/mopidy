import pathlib
import shutil
import tempfile
import unittest

import pytest

from mopidy.internal import path
from mopidy.internal.gi import GLib


class GetOrCreateDirTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.parent = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):  # noqa: N802
        if self.parent.is_dir():
            shutil.rmtree(str(self.parent))

    def test_creating_dir(self):
        dir_path = self.parent / "test"
        assert not dir_path.exists()

        created = path.get_or_create_dir(str(dir_path))

        assert dir_path.is_dir()
        assert created == dir_path

    def test_creating_nested_dirs(self):
        level2_dir = self.parent / "test"
        level3_dir = self.parent / "test" / "test"
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
        conflicting_file = self.parent / "test"
        conflicting_file.touch()
        dir_path = self.parent / "test"

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
        file_path = self.parent / "test"
        assert not file_path.exists()

        created = path.get_or_create_file(str(file_path))

        assert file_path.is_file()
        assert created == file_path

    def test_creating_nested_file(self):
        level2_dir = self.parent / "test"
        file_path = self.parent / "test" / "test"
        assert not level2_dir.exists()
        assert not file_path.exists()

        created = path.get_or_create_file(str(file_path))

        assert level2_dir.is_dir()
        assert file_path.is_file()
        assert created == file_path

    def test_creating_existing_file(self):
        file_path = self.parent / "test"
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
        file_path = self.parent / "foo" / "bar"

        with pytest.raises(OSError):
            path.get_or_create_file(file_path, mkdir=False)

    def test_create_dir_with_bytes_content(self):
        file_path = self.parent / "test"

        created = path.get_or_create_file(str(file_path), content=b"foobar")

        assert created.read_bytes() == b"foobar"

    def test_create_dir_with_unicode_content(self):
        file_path = self.parent / "test"

        created = path.get_or_create_file(str(file_path), content="foobaræøå")
        assert created.read_bytes() == b"foobar\xc3\xa6\xc3\xb8\xc3\xa5"


class GetUnixSocketPathTest(unittest.TestCase):
    def test_correctly_matched_socket_path(self):
        assert (
            path.get_unix_socket_path("unix:/tmp/mopidy.socket")
            == "/tmp/mopidy.socket"
        )

    def test_correctly_no_match_socket_path(self):
        assert path.get_unix_socket_path("127.0.0.1") is None


class PathToFileURITest(unittest.TestCase):
    def test_simple_path(self):
        result = path.path_to_uri("/etc/fstab")

        assert result == "file:///etc/fstab"

    def test_space_in_path(self):
        result = path.path_to_uri("/tmp/test this")

        assert result == "file:///tmp/test%20this"

    def test_unicode_in_path(self):
        result = path.path_to_uri("/tmp/æøå")

        assert result == "file:///tmp/%C3%A6%C3%B8%C3%A5"


class UriToPathTest(unittest.TestCase):
    def test_simple_uri(self):
        result = path.uri_to_path("file:///etc/fstab")

        assert result == pathlib.Path("/etc/fstab")

    def test_space_in_uri(self):
        result = path.uri_to_path("file:///tmp/test%20this")

        assert result == pathlib.Path("/tmp/test this")

    def test_unicode_in_uri(self):
        result = path.uri_to_path("file:///tmp/%C3%A6%C3%B8%C3%A5")

        assert result == pathlib.Path("/tmp/æøå")

    def test_latin1_in_uri(self):
        result = path.uri_to_path("file:///tmp/%E6%F8%E5")

        assert bytes(result) == b"/tmp/\xe6\xf8\xe5"


class ExpandPathTest(unittest.TestCase):
    def test_empty_path(self):
        result = path.expand_path("")

        assert result == pathlib.Path(".").resolve()

    def test_absolute_path(self):
        result = path.expand_path("/tmp/foo")

        assert result == pathlib.Path("/tmp/foo")

    def test_home_dir_expansion(self):
        result = path.expand_path("~/foo")

        assert result == pathlib.Path("~/foo").expanduser()

    def test_abspath(self):
        result = path.expand_path("./foo")

        assert result == pathlib.Path("./foo").resolve()

    def test_xdg_subsititution(self):
        expected = GLib.get_user_data_dir() + "/foo"
        result = path.expand_path("$XDG_DATA_DIR/foo")

        assert str(result) == expected

    def test_xdg_subsititution_unknown(self):
        result = path.expand_path("/tmp/$XDG_INVALID_DIR/foo")

        assert result is None

    def test_invalid_utf8_bytes(self):
        result = path.expand_path(b"ab\xc3\x12")

        assert result == pathlib.Path("ab\udcc3\x12").resolve()


class TestIsPathInsideBaseDir:
    def test_when_inside(self):
        assert path.is_path_inside_base_dir("/æ/øå", "/æ")

    def test_when_outside(self):
        assert not path.is_path_inside_base_dir("/æ/øå", "/ø")

    def test_byte_inside_str_does_not_fail(self):
        assert path.is_path_inside_base_dir("/æ/øå".encode(), "/æ")

    def test_str_inside_byte_does_not_fail(self):
        assert path.is_path_inside_base_dir("/æ/øå", "/æ".encode())

    def test_str_inside_str_fails_does_not_fail(self):
        assert path.is_path_inside_base_dir("/æ/øå", "/æ")

    def test_bytes_inside_bytes_fails_does_not_fail(self):
        assert path.is_path_inside_base_dir("/æ/øå".encode(), "/æ".encode())
