import io
import pathlib

import pytest

from mopidy.m3u import translator
from mopidy.m3u.translator import path_to_uri
from mopidy.models import Playlist, Ref, Track


def loads(s, basedir):
    return translator.load_items(io.StringIO(s), basedir)


def dumps(items):
    fp = io.StringIO()
    translator.dump_items(items, fp)
    return fp.getvalue()


@pytest.mark.parametrize(
    "path,scheme,expected",
    [
        ("test", None, "m3u:test"),
        ("test.m3u", None, "m3u:test.m3u"),
        ("./test.m3u", None, "m3u:test.m3u"),
        ("foo/../test.m3u", None, "m3u:test.m3u"),
        ("Test Playlist.m3u", None, "m3u:Test%20Playlist.m3u"),
        ("test.mp3", "file", "file:///test.mp3"),
    ],
)
def test_path_to_uri(path, scheme, expected):
    if scheme is not None:
        assert path_to_uri(pathlib.Path(path), scheme) == expected
    else:
        assert path_to_uri(pathlib.Path(path)) == expected


def test_latin1_path_to_uri():
    bytes_path = "æøå.m3u".encode("latin-1")
    path = pathlib.Path(bytes_path.decode(errors="surrogateescape"))

    assert translator.path_to_uri(path) == "m3u:%E6%F8%E5.m3u"


def test_utf8_path_to_uri():
    bytes_path = "æøå.m3u".encode()
    path = pathlib.Path(bytes_path.decode())

    assert translator.path_to_uri(path) == "m3u:%C3%A6%C3%B8%C3%A5.m3u"


@pytest.mark.parametrize(
    "path,expected",
    [
        ("test", "test"),
        ("test.m3u", "test"),
        ("../test.m3u", "test"),
        ("testæ.m3u", "testæ"),
    ],
)
def test_name_from_path(path, expected):
    assert translator.name_from_path(pathlib.Path(path)) == expected


def test_path_from_name():
    from mopidy.m3u.translator import path_from_name

    assert path_from_name("test") == pathlib.Path("test")
    assert path_from_name("test", ".m3u") == pathlib.Path("test.m3u")
    assert path_from_name("foo/bar", sep="-") == pathlib.Path("foo-bar")


@pytest.mark.parametrize(
    "path,expected",
    [
        ("test.m3u", ("m3u:test.m3u", "test")),
        ("Test Playlist.m3u", ("m3u:Test%20Playlist.m3u", "Test Playlist")),
    ],
)
def test_path_to_ref(path, expected):
    from mopidy.m3u.translator import path_to_ref

    result = path_to_ref(pathlib.Path(path))
    assert Ref.playlist(uri=expected[0], name=expected[1]) == result


@pytest.mark.parametrize(
    "contents,basedir,expected",
    [
        ("", ".", None),
        ("test.mp3", "/playlists", ("file:///playlists/test.mp3", "test")),
        ("../test.mp3", "/playlists", ("file:///test.mp3", "test")),
        ("/test.mp3", ".", ("file:///test.mp3", "test")),
        ("file:///test.mp3", ".", ("file:///test.mp3", None)),
        ("http://example.com/stream", ".", ("http://example.com/stream", None)),
        (
            "#EXTM3U\n#EXTINF:42,Test\nfile:///test.mp3\n",
            ".",
            ("file:///test.mp3", "Test"),
        ),
        (
            "#EXTM3U\n#EXTINF:-1,Test\nhttp://example.com/stream\n",
            ".",
            ("http://example.com/stream", "Test"),
        ),
    ],
)
def test_load_items(contents, basedir, expected):
    result = loads(contents, pathlib.Path(basedir))
    if expected is not None:
        assert [Ref.track(uri=expected[0], name=expected[1])] == result
    else:
        assert [] == result


def test_dump_items():
    assert dumps([]) == ""
    assert dumps([Ref.track(uri="file:///test.mp3")]) == ("file:///test.mp3\n")
    assert dumps([Ref.track(uri="file:///test.mp3", name="test")]) == (
        "#EXTM3U\n" "#EXTINF:-1,test\n" "file:///test.mp3\n"
    )
    assert dumps([Track(uri="file:///test.mp3", name="test", length=42)]) == (
        "#EXTM3U\n" "#EXTINF:-1,test\n" "file:///test.mp3\n"
    )
    assert dumps([Track(uri="http://example.com/stream")]) == (
        "http://example.com/stream\n"
    )
    assert dumps([Track(uri="http://example.com/stream", name="Test")]) == (
        "#EXTM3U\n" "#EXTINF:-1,Test\n" "http://example.com/stream\n"
    )


def test_playlist():
    from mopidy.m3u.translator import playlist

    path = pathlib.Path("test.m3u")

    assert playlist(path) == Playlist(uri="m3u:test.m3u", name="test")
    assert playlist(path, [Ref(uri="file:///test.mp3")], 1) == Playlist(
        uri="m3u:test.m3u",
        name="test",
        tracks=[Track(uri="file:///test.mp3")],
        last_modified=1000,
    )
