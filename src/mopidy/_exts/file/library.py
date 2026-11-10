import itertools
import logging
import mimetypes
import os
import pathlib
import urllib.parse
from collections.abc import Generator, Iterable
from typing import TypedDict, cast, override

from mopidy import backend
from mopidy import config as config_lib
from mopidy._lib import paths
from mopidy.media import MediaReader
from mopidy.models import Image, ImageData, Ref, Track
from mopidy.types import Uri

from . import Extension
from .types import FileConfig

logger = logging.getLogger(__name__)

COVER_NAMES = ("cover", "folder", "front", "album")
"""The names of cover image files, in order of preference."""

COVER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
"""The file extensions of cover image files, in order of preference."""

_COVER_FILE_NAMES = {
    f"{name}{ext}": priority
    for priority, (name, ext) in enumerate(
        itertools.product(COVER_NAMES, COVER_EXTENSIONS)
    )
}
"""Lower case cover file names, mapped to their order of preference."""


class MediaDir(TypedDict):
    path: pathlib.Path
    name: str


class FileLibraryProvider(backend.LibraryProvider):
    """Library for browsing local files."""

    # TODO: get_images that can pull from embedded metadata?
    # TODO: handle playlists?

    def __init__(
        self,
        backend: backend.Backend,
        config: config_lib.Config,
        media_reader: MediaReader,
    ) -> None:
        super().__init__(backend)

        ext_config = cast(FileConfig, config[Extension.ext_name])

        self._media_dirs = list(self._get_media_dirs(config))
        self._show_dotfiles = ext_config["show_dotfiles"]
        self._excluded_file_extensions = tuple(
            file_ext.lower() for file_ext in ext_config["excluded_file_extensions"]
        )
        self._follow_symlinks = ext_config["follow_symlinks"]

        self._media_reader = media_reader

        self.root_directory = self._get_root_directory()

    @override
    def browse(self, uri: Uri) -> list[Ref]:  # noqa: C901
        logger.debug("Browsing files at: %s", uri)
        result = []
        local_path = paths.uri_to_path(uri)

        if str(local_path) == "root":
            return list(self._get_media_dirs_refs())

        if not self._is_in_basedir(local_path):
            logger.warning(
                "Rejected attempt to browse path (%s) outside dirs defined "
                "in file/media_dirs config.",
                uri,
            )
            return []
        if paths.uri_to_path(uri).is_file():
            logger.error("Rejected attempt to browse file (%s)", uri)
            return []

        for dir_entry in local_path.iterdir():
            child_path = dir_entry.resolve()
            uri = paths.path_to_uri(child_path)

            if not self._show_dotfiles and dir_entry.name.startswith("."):
                continue

            if (
                self._excluded_file_extensions
                and dir_entry.suffix.lower() in self._excluded_file_extensions
            ):
                continue

            if dir_entry.is_symlink() and not self._follow_symlinks:
                logger.debug("Ignoring symlink: %s", uri)
                continue

            if not self._is_in_basedir(child_path):
                logger.debug("Ignoring symlink to outside base dir: %s", uri)
                continue

            if child_path.is_dir():
                result.append(Ref.directory(name=dir_entry.name, uri=uri))
            elif child_path.is_file():
                result.append(Ref.track(name=dir_entry.name, uri=uri))

        def order(ref: Ref) -> tuple:
            return (ref.type != Ref.DIRECTORY, ref.name)

        result.sort(key=order)

        return result

    @override
    def lookup(self, uri: Uri) -> list[Track]:
        logger.debug("Looking up file URI: %s", uri)
        local_path = paths.uri_to_path(uri)

        if not self._is_in_basedir(local_path):
            logger.warning(
                "Rejected attempt to look up path (%s) outside dirs defined "
                "in file/media_dirs config.",
                uri,
            )
            return []

        target = self._media_reader.find_playback_target(uri)
        if target and target.info:
            track = target.info.track.replace(uri=uri)
        else:
            logger.warning("Failed looking up %s", uri)
            track = Track(uri=uri)

        if not track.name:
            track = track.replace(
                name=local_path.name,
            )

        return [track]

    @override
    def get_images(self, uris: Iterable[Uri]) -> dict[Uri, list[Image]]:
        """Get the cover image files in the directory of each URI.

        For a directory URI, the cover images are looked up in the directory
        itself. For a file URI, they are looked up in the file's directory.
        """
        covers_by_dir: dict[pathlib.Path, list[Image]] = {}
        result: dict[Uri, list[Image]] = {}
        for uri in uris:
            local_path = paths.uri_to_path(uri)
            if not self._is_in_basedir(local_path):
                continue
            dir_path = local_path if local_path.is_dir() else local_path.parent
            if dir_path not in covers_by_dir:
                covers_by_dir[dir_path] = [
                    Image(uri=paths.path_to_uri(path))
                    for path in self._find_cover_files(dir_path)
                ]
            if covers_by_dir[dir_path]:
                result[uri] = covers_by_dir[dir_path]
        return result

    @override
    def get_image_data(
        self,
        uri: Uri,
        image_uri: str,
        max_size: int,
    ) -> ImageData | None:
        if urllib.parse.urlsplit(image_uri).scheme != "file":
            return None
        image_path = paths.uri_to_path(image_uri)
        if not self._is_in_basedir(image_path):
            logger.warning(
                "Rejected attempt to read image (%s) outside dirs defined "
                "in file/media_dirs config.",
                image_uri,
            )
            return None
        try:
            if image_path.stat().st_size > max_size:
                logger.warning("Image is too large to read: %s", image_uri)
                return None
            data = image_path.read_bytes()
        except OSError as exc:
            logger.warning("Failed reading image %s: %s", image_uri, exc)
            return None
        mime_type, _ = mimetypes.guess_type(image_path.name)
        return ImageData(data=data, mime_type=mime_type)

    def _find_cover_files(self, dir_path: pathlib.Path) -> list[pathlib.Path]:
        try:
            dir_entries = list(dir_path.iterdir())
        except OSError as exc:
            logger.debug("Failed looking for cover images in %s: %s", dir_path, exc)
            return []
        covers = [
            dir_entry
            for dir_entry in dir_entries
            if dir_entry.name.lower() in _COVER_FILE_NAMES
            and (self._follow_symlinks or not dir_entry.is_symlink())
            and dir_entry.is_file()
            and self._is_in_basedir(dir_entry.resolve())
        ]
        return sorted(
            covers,
            key=lambda path: (_COVER_FILE_NAMES[path.name.lower()], path.name),
        )

    def _get_root_directory(self) -> Ref | None:
        if not self._media_dirs:
            return None
        if len(self._media_dirs) == 1:
            uri = paths.path_to_uri(self._media_dirs[0]["path"])
        else:
            uri = Uri("file:root")
        return Ref.directory(name="Files", uri=uri)

    def _get_media_dirs(self, config: config_lib.Config) -> Generator[MediaDir]:
        for entry in config["file"]["media_dirs"]:
            media_dir_split = [part.strip() for part in entry.split("|", 1)]
            local_path = paths.expand_path(media_dir_split[0])

            if local_path is None:
                logger.debug(
                    "Failed expanding path (%s) from file/media_dirs config value.",
                    media_dir_split[0],
                )
                continue
            elif not local_path.is_dir():
                logger.warning(
                    "%s is not a directory. Please create the directory or "
                    "update the file/media_dirs config value.",
                    local_path.as_uri(),
                )
                continue

            if len(media_dir_split) == 2:
                name = media_dir_split[1]
            else:
                # TODO: MPD client should accept `/` in dir name
                name = media_dir_split[0].replace(os.sep, "+")

            yield MediaDir(path=local_path, name=name)

    def _get_media_dirs_refs(self) -> Generator[Ref]:
        for media_dir in self._media_dirs:
            yield Ref.directory(
                name=media_dir["name"],
                uri=paths.path_to_uri(media_dir["path"]),
            )

    def _is_in_basedir(self, local_path: pathlib.Path) -> bool:
        return any(
            paths.is_path_inside_base_dir(local_path, media_dir["path"])
            for media_dir in self._media_dirs
        )
