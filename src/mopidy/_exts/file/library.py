import logging
import os
import pathlib
from collections.abc import Generator
from typing import TypedDict, cast, override

from mopidy import backend
from mopidy import config as config_lib
from mopidy._lib import paths
from mopidy.media import MediaReader
from mopidy.models import Ref, Track
from mopidy.types import Uri

from . import Extension
from .cue_library import (
    CueAlbum,
    CueLibrary,
    is_cue_path,
    make_track_uri,
    split_cue_uri,
)
from .types import FileConfig

logger = logging.getLogger(__name__)


class MediaDir(TypedDict):
    path: pathlib.Path
    name: str


class FileLibraryProvider(backend.LibraryProvider):
    """Library for browsing local files."""

    # TODO: get_images that can pull from metadata and/or .folder.png etc?
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
        self.cue_library = (
            CueLibrary(
                media_reader=media_reader,
                encodings=ext_config["cue_encodings"],
                is_allowed=self._is_cue_audio_file_allowed,
            )
            if ext_config["cue_sheets"]
            else None
        )

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
        if (
            self.cue_library
            and local_path.is_file()
            and (cue_uri := split_cue_uri(uri))
        ):
            return self._browse_cue(cue_uri[0], local_path, cue_uri[1])
        if local_path.is_file():
            logger.error("Rejected attempt to browse file (%s)", uri)
            return []

        entries = list(self._visible_entries(local_path))

        # A CUE sheet is shown as a directory with the tracks of the sheet, and
        # the audio files that it describes are hidden.
        albums, hidden = self._find_cue_albums([path for _, path in entries])

        for dir_entry, child_path in entries:
            uri = paths.path_to_uri(child_path)
            if child_path in albums:
                name = albums[child_path].sheet.title or dir_entry.stem
                result.append(Ref.directory(name=name, uri=uri))
            elif child_path in hidden:
                continue
            elif child_path.is_dir():
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

        if self.cue_library and local_path.is_file() and split_cue_uri(uri):
            return self._lookup_cue(uri, local_path)

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

    def _visible_entries(
        self, local_path: pathlib.Path
    ) -> Generator[tuple[pathlib.Path, pathlib.Path]]:
        """Get the entries of a directory that the config says to show.

        Yields each entry, and the entry with symlinks resolved.
        """
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

            yield dir_entry, child_path

    def _find_cue_albums(
        self, child_paths: list[pathlib.Path]
    ) -> tuple[dict[pathlib.Path, CueAlbum], set[pathlib.Path]]:
        """Find the usable CUE sheets, and the audio files that they describe."""
        albums: dict[pathlib.Path, CueAlbum] = {}
        hidden: set[pathlib.Path] = set()
        if self.cue_library is None:
            return albums, hidden
        for child_path in child_paths:
            if not (is_cue_path(child_path) and child_path.is_file()):
                continue
            if (album := self.cue_library.load(child_path)) is not None:
                albums[child_path] = album
                hidden |= album.audio_paths
        return albums, hidden

    def _browse_cue(
        self,
        sheet_uri: Uri,
        local_path: pathlib.Path,
        track_position: int | None,
    ) -> list[Ref]:
        assert self.cue_library
        if track_position is not None:
            logger.error("Rejected attempt to browse track (%s)", sheet_uri)
            return []
        album = self.cue_library.load(local_path)
        if album is None:
            return []
        return [
            Ref.track(
                name=(
                    f"{target.track.number:02d} - {target.track.title}"
                    if target.track.title
                    else f"Track {target.track.number:02d}"
                ),
                uri=make_track_uri(sheet_uri, target.position),
            )
            for target in album.targets
        ]

    def _lookup_cue(self, uri: Uri, local_path: pathlib.Path) -> list[Track]:
        assert self.cue_library
        sheet_uri, position = split_cue_uri(uri) or (uri, None)
        album = self.cue_library.load(local_path)
        if album is None:
            logger.warning("Failed looking up %s", sheet_uri)
            return []
        tracks = self.cue_library.make_tracks(album, position)
        if not tracks:
            logger.warning("Failed looking up %s", uri)
        return tracks

    def _is_cue_audio_file_allowed(self, audio_path: pathlib.Path) -> bool:
        """Check if a CUE sheet can use a file, which can be anywhere it names."""
        if audio_path.is_symlink() and not self._follow_symlinks:
            return False
        return self._is_in_basedir(audio_path)

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
