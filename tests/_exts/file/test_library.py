from unittest import mock

import pykka
import pytest

from mopidy._exts.file import backend
from mopidy._lib.paths import path_to_uri
from mopidy.core import Core
from mopidy.models import Image, ImageData

JPEG = b"\xff\xd8\xff\xe0jpeg"
PNG = b"\x89PNG\r\n\x1a\npng"
MAX_SIZE = 1024


@pytest.fixture
def music_dir(tmp_path):
    music_dir = tmp_path / "music"
    album_dir = music_dir / "album"
    album_dir.mkdir(parents=True)
    (album_dir / "song.mp3").write_bytes(b"")
    return music_dir


@pytest.fixture
def media_dirs(music_dir):
    return [str(music_dir)]


@pytest.fixture
def album_dir(music_dir):
    return music_dir / "album"


@pytest.fixture
def track_uri(album_dir):
    return path_to_uri(album_dir / "song.mp3")


def test_get_images_finds_cover_in_track_dir(provider, album_dir, track_uri):
    (album_dir / "cover.jpg").write_bytes(JPEG)

    result = provider.get_images([track_uri])

    assert result == {track_uri: [Image(uri=path_to_uri(album_dir / "cover.jpg"))]}


def test_get_images_finds_cover_in_dir(provider, album_dir):
    (album_dir / "folder.png").write_bytes(PNG)
    dir_uri = path_to_uri(album_dir)

    result = provider.get_images([dir_uri])

    assert result == {dir_uri: [Image(uri=path_to_uri(album_dir / "folder.png"))]}


def test_get_images_matches_names_case_insensitively(provider, album_dir, track_uri):
    (album_dir / "Cover.JPG").write_bytes(JPEG)

    result = provider.get_images([track_uri])

    assert result == {track_uri: [Image(uri=path_to_uri(album_dir / "Cover.JPG"))]}


def test_get_images_orders_covers_by_preference(provider, album_dir, track_uri):
    for name in ["album.jpg", "folder.jpg", "cover.png", "cover.jpg"]:
        (album_dir / name).write_bytes(JPEG)

    result = provider.get_images([track_uri])

    assert [image.uri for image in result[track_uri]] == [
        path_to_uri(album_dir / name)
        for name in ["cover.jpg", "cover.png", "folder.jpg", "album.jpg"]
    ]


def test_get_images_ignores_other_files(provider, album_dir, track_uri):
    (album_dir / "back.jpg").write_bytes(JPEG)
    (album_dir / "cover.txt").write_bytes(b"")
    (album_dir / "cover.jpg").mkdir()

    assert provider.get_images([track_uri]) == {}


def test_get_images_ignores_excluded_file_extensions(provider, album_dir, track_uri):
    # The default config excludes image files from browsing, but not as covers.
    provider._excluded_file_extensions = (".jpg",)
    (album_dir / "cover.jpg").write_bytes(JPEG)

    assert track_uri in provider.get_images([track_uri])


def test_get_images_omits_uris_without_covers(provider, album_dir, track_uri):
    other_dir = album_dir.parent / "other"
    other_dir.mkdir()
    (other_dir / "song.mp3").write_bytes(b"")
    (album_dir / "cover.jpg").write_bytes(JPEG)
    other_uri = path_to_uri(other_dir / "song.mp3")

    result = provider.get_images([track_uri, other_uri])

    assert list(result) == [track_uri]


def test_get_images_ignores_uris_outside_media_dirs(provider, tmp_path):
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "cover.jpg").write_bytes(JPEG)

    assert provider.get_images([path_to_uri(outside_dir / "song.mp3")]) == {}


def test_get_images_ignores_symlinked_covers(provider, album_dir, track_uri):
    (album_dir / "real.jpg").write_bytes(JPEG)
    (album_dir / "cover.jpg").symlink_to(album_dir / "real.jpg")

    assert provider.get_images([track_uri]) == {}


@pytest.mark.parametrize("follow_symlinks", [True])
def test_get_images_follows_symlinked_covers_if_enabled(provider, album_dir, track_uri):
    (album_dir / "real.jpg").write_bytes(JPEG)
    (album_dir / "cover.jpg").symlink_to(album_dir / "real.jpg")

    result = provider.get_images([track_uri])

    assert result == {track_uri: [Image(uri=path_to_uri(album_dir / "cover.jpg"))]}


@pytest.mark.parametrize("follow_symlinks", [True])
def test_get_images_ignores_symlinks_to_outside_media_dirs(
    provider, album_dir, track_uri, tmp_path
):
    (tmp_path / "secret.jpg").write_bytes(JPEG)
    (album_dir / "cover.jpg").symlink_to(tmp_path / "secret.jpg")

    assert provider.get_images([track_uri]) == {}


def test_get_image_data_reads_cover(provider, album_dir, track_uri):
    (album_dir / "cover.jpg").write_bytes(JPEG)

    result = provider.get_image_data(
        track_uri, path_to_uri(album_dir / "cover.jpg"), MAX_SIZE
    )

    assert result == ImageData(data=JPEG, mime_type="image/jpeg")


def test_get_image_data_guesses_png_mime_type(provider, album_dir, track_uri):
    (album_dir / "folder.png").write_bytes(PNG)

    result = provider.get_image_data(
        track_uri, path_to_uri(album_dir / "folder.png"), MAX_SIZE
    )

    assert result == ImageData(data=PNG, mime_type="image/png")


def test_get_image_data_rejects_path_outside_media_dirs(provider, tmp_path, track_uri):
    (tmp_path / "secret.jpg").write_bytes(JPEG)

    assert (
        provider.get_image_data(
            track_uri, path_to_uri(tmp_path / "secret.jpg"), MAX_SIZE
        )
        is None
    )


def test_get_image_data_rejects_non_file_uri(provider, track_uri):
    assert (
        provider.get_image_data(track_uri, "https://example.com/a.jpg", MAX_SIZE)
        is None
    )


def test_get_image_data_returns_none_for_missing_file(provider, album_dir, track_uri):
    assert (
        provider.get_image_data(
            track_uri, path_to_uri(album_dir / "cover.jpg"), MAX_SIZE
        )
        is None
    )


def test_get_image_data_returns_none_for_too_large_file(provider, album_dir, track_uri):
    (album_dir / "cover.jpg").write_bytes(JPEG)

    assert (
        provider.get_image_data(
            track_uri, path_to_uri(album_dir / "cover.jpg"), len(JPEG) - 1
        )
        is None
    )


def test_get_image_data_reads_file_of_max_size(provider, album_dir, track_uri):
    (album_dir / "cover.jpg").write_bytes(JPEG)

    result = provider.get_image_data(
        track_uri, path_to_uri(album_dir / "cover.jpg"), len(JPEG)
    )

    assert result == ImageData(data=JPEG, mime_type="image/jpeg")


@pytest.fixture
def core(config):
    file_backend = backend.FileBackend.start(config=config, audio=mock.Mock()).proxy()
    yield Core.start(config=config, backends=[file_backend]).proxy()
    pykka.ActorRegistry.stop_all()


def test_core_get_image_data_reads_cover_from_file_backend(core, album_dir, track_uri):
    (album_dir / "cover.jpg").write_bytes(JPEG)

    images = core.library.get_images([track_uri]).get()
    result = core.library.get_image_data(track_uri, images[track_uri][0].uri).get()

    assert result == ImageData(data=JPEG, mime_type="image/jpeg")


def test_core_get_image_data_rejects_files_that_are_not_covers(
    core, album_dir, track_uri
):
    (album_dir / "cover.jpg").write_bytes(JPEG)

    result = core.library.get_image_data(track_uri, track_uri).get()

    assert result is None
