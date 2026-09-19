import pathlib

import pytest

from mopidy._lib import paths
from mopidy._lib.gi import GLib


@pytest.fixture
def parent(tmp_path):
    return tmp_path.resolve()


def test_get_or_create_dir_creating_dir(parent):
    dir_path = parent / "test"
    assert not dir_path.exists()

    created = paths.get_or_create_dir(str(dir_path))

    assert dir_path.is_dir()
    assert created == dir_path


def test_get_or_create_dir_creating_nested_dirs(parent):
    level2_dir = parent / "test"
    level3_dir = parent / "test" / "test"
    assert not level2_dir.exists()
    assert not level3_dir.exists()

    created = paths.get_or_create_dir(str(level3_dir))

    assert level2_dir.is_dir()
    assert level3_dir.is_dir()
    assert created == level3_dir


def test_get_or_create_dir_creating_existing_dir(parent):
    created = paths.get_or_create_dir(str(parent))

    assert parent.is_dir()
    assert created == parent


def test_get_or_create_dir_create_dir_with_name_of_existing_file_throws_oserror(
    parent,
):
    conflicting_file = parent / "test"
    conflicting_file.touch()
    dir_path = parent / "test"

    with pytest.raises(OSError):
        paths.get_or_create_dir(str(dir_path))


def test_get_or_create_dir_create_dir_with_none():
    with pytest.raises(TypeError):
        paths.get_or_create_dir(None)  # pyright: ignore[reportArgumentType]


def test_get_or_create_file_creating_file(parent):
    file_path = parent / "test"
    assert not file_path.exists()

    created = paths.get_or_create_file(str(file_path))

    assert file_path.is_file()
    assert created == file_path


def test_get_or_create_file_creating_nested_file(parent):
    level2_dir = parent / "test"
    file_path = parent / "test" / "test"
    assert not level2_dir.exists()
    assert not file_path.exists()

    created = paths.get_or_create_file(str(file_path))

    assert level2_dir.is_dir()
    assert file_path.is_file()
    assert created == file_path


def test_get_or_create_file_creating_existing_file(parent):
    file_path = parent / "test"
    paths.get_or_create_file(str(file_path))

    created = paths.get_or_create_file(str(file_path))

    assert file_path.is_file()
    assert created == file_path


def test_get_or_create_file_create_file_with_name_of_existing_dir_throws_error(
    parent,
):
    with pytest.raises(OSError):
        paths.get_or_create_file(parent)


def test_get_or_create_file_create_file_with_none_filename_throws_type_error():
    with pytest.raises(TypeError):
        paths.get_or_create_file(None)  # pyright: ignore[reportArgumentType]


def test_get_or_create_file_create_dir_without_mkdir(parent):
    file_path = parent / "foo" / "bar"

    with pytest.raises(OSError):
        paths.get_or_create_file(file_path, mkdir=False)


def test_get_or_create_file_create_dir_with_bytes_content(parent):
    file_path = parent / "test"

    created = paths.get_or_create_file(str(file_path), content=b"foobar")

    assert created.read_bytes() == b"foobar"


def test_get_or_create_file_create_dir_with_unicode_content(parent):
    file_path = parent / "test"

    created = paths.get_or_create_file(str(file_path), content="foobaræøå")
    assert created.read_bytes() == b"foobar\xc3\xa6\xc3\xb8\xc3\xa5"


def test_get_unix_socket_path_correctly_matched_socket_path():
    assert paths.get_unix_socket_path("unix:/tmp/mopidy.socket") == pathlib.Path(
        "/tmp/mopidy.socket",
    )


def test_get_unix_socket_path_correctly_no_match_socket_path():
    assert paths.get_unix_socket_path("127.0.0.1") is None


def test_path_to_uri_simple_path():
    result = paths.path_to_uri("/etc/fstab")

    assert result == "file:///etc/fstab"


def test_path_to_uri_space_in_path():
    result = paths.path_to_uri("/tmp/test this")

    assert result == "file:///tmp/test%20this"


def test_path_to_uri_unicode_in_path():
    result = paths.path_to_uri("/tmp/æøå")

    assert result == "file:///tmp/%C3%A6%C3%B8%C3%A5"


def test_uri_to_path_simple_uri():
    result = paths.uri_to_path("file:///etc/fstab")

    assert result == pathlib.Path("/etc/fstab")


def test_uri_to_path_space_in_uri():
    result = paths.uri_to_path("file:///tmp/test%20this")

    assert result == pathlib.Path("/tmp/test this")


def test_uri_to_path_unicode_in_uri():
    result = paths.uri_to_path("file:///tmp/%C3%A6%C3%B8%C3%A5")

    assert result == pathlib.Path("/tmp/æøå")


def test_uri_to_path_latin1_in_uri():
    result = paths.uri_to_path("file:///tmp/%E6%F8%E5")

    assert bytes(result) == b"/tmp/\xe6\xf8\xe5"


def test_expand_path_empty_path():
    result = paths.expand_path("")

    assert result == pathlib.Path.cwd()


def test_expand_path_absolute_path():
    result = paths.expand_path("/tmp/foo")

    assert result == pathlib.Path("/tmp/foo").resolve()


def test_expand_path_home_dir_expansion():
    result = paths.expand_path("~/foo")

    assert result == pathlib.Path("~/foo").expanduser()


def test_expand_path_abspath():
    result = paths.expand_path("./foo")

    assert result == pathlib.Path("./foo").resolve()


def test_expand_path_xdg_subsititution():
    expected = GLib.get_user_data_dir() + "/foo"
    result = paths.expand_path("$XDG_DATA_DIR/foo")

    assert str(result) == expected


def test_expand_path_xdg_subsititution_unknown():
    with pytest.raises(ValueError) as exc_info:
        paths.expand_path("/tmp/$XDG_INVALID_DIR/foo")

    assert str(exc_info.value) == (
        "Unexpanded '$...' in path '/tmp/$XDG_INVALID_DIR/foo'"
    )


def test_expand_path_invalid_utf8_bytes():
    result = paths.expand_path(b"ab\xc3\x12")

    assert result == pathlib.Path("ab\udcc3\x12").resolve()


def test_is_path_inside_base_dir_when_inside():
    assert paths.is_path_inside_base_dir("/æ/øå", "/æ")


def test_is_path_inside_base_dir_when_outside():
    assert not paths.is_path_inside_base_dir("/æ/øå", "/ø")


def test_is_path_inside_base_dir_byte_inside_str_does_not_fail():
    assert paths.is_path_inside_base_dir("/æ/øå".encode(), "/æ")


def test_is_path_inside_base_dir_str_inside_byte_does_not_fail():
    assert paths.is_path_inside_base_dir("/æ/øå", "/æ".encode())


def test_is_path_inside_base_dir_str_inside_str_fails_does_not_fail():
    assert paths.is_path_inside_base_dir("/æ/øå", "/æ")


def test_is_path_inside_base_dir_bytes_inside_bytes_fails_does_not_fail():
    assert paths.is_path_inside_base_dir("/æ/øå".encode(), "/æ".encode())
