from __future__ import annotations

import contextlib
import locale
import logging
import operator
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, cast

from mopidy import backend
from mopidy.exceptions import BackendError
from mopidy.internal import path
from mopidy.m3u.types import M3UConfig

from . import Extension, translator

if TYPE_CHECKING:
    from mopidy.backend import Backend
    from mopidy.ext import Config
    from mopidy.models import Playlist, Ref
    from mopidy.types import Uri

logger = logging.getLogger(__name__)

# Function to log an environment error with formatted message and error details
def log_environment_error(message: str, error: EnvironmentError) -> None:
    if isinstance(error.strerror, bytes):
        strerror = error.strerror.decode(locale.getpreferredencoding())
    else:
        strerror = error.strerror
    logger.error("%s: %s", message, strerror)

# Context manager to safely replace a file atomically
@contextlib.contextmanager
def replace(
    path: Path,
    mode: str = "w+b",
    encoding: str | None = None,
    errors: str | None = None,
) -> Generator[IO[Any], None, None]:
    (fd, tempname) = tempfile.mkstemp(dir=str(path.parent))
    tempname = Path(tempname)
    try:
        fp = open(fd, mode, encoding=encoding, errors=errors)  # noqa: PTH123, SIM115
    except Exception:
        tempname.unlink()
        os.close(fd)
        raise
    try:
        yield fp
        fp.flush()
        os.fsync(fd)
        tempname.rename(path)
    except Exception:
        tempname.unlink()
        raise
    finally:
        fp.close()

# PlaylistsProvider class handling M3U playlists for the backend
class M3UPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, backend: Backend, config: Config) -> None:
        super().__init__(backend)

        ext_config = cast(M3UConfig, config[Extension.ext_name])
        
        # Initialize various configurations for M3U playlists
        self._playlists_dir = (
            path.expand_path(ext_config["playlists_dir"])
            if ext_config["playlists_dir"]
            else Extension.get_data_dir(config)
        )
        self._base_dir = (
            path.expand_path(ext_config["base_dir"])
            if ext_config["base_dir"]
            else self._playlists_dir
        )
        self._default_encoding = ext_config["default_encoding"]
        self._default_extension = ext_config["default_extension"]

    # Retrieve playlists as a sorted list of references
    def as_list(self) -> list[Ref]:
        # Logic to fetch playlists and sort them alphabetically
        result = []
        for entry in self._playlists_dir.iterdir():
            if entry.suffix not in [".m3u", ".m3u8"]:
                continue
            if not entry.is_file():
                continue
            playlist_path = entry.relative_to(self._playlists_dir)
            result.append(translator.path_to_ref(playlist_path))
        result.sort(key=operator.attrgetter("name"))
        return result

    # Create an empty playlist with the provided name
    def create(self, name: str) -> Playlist | None:
        # Logic to create an empty playlist with error handling
        path = translator.path_from_name(name.strip(), self._default_extension)
        try:
            with self._open(path, "w"):
                pass
            mtime = self._abspath(path).stat().st_mtime
        except OSError as e:
            log_environment_error(f"Error creating playlist {name!r}", e)
        else:
            return translator.playlist(path, [], mtime)

    # Delete a playlist identified by its URI
    def delete(self, uri: Uri) -> bool:
        # Logic to delete a playlist with error handling
        path = translator.uri_to_path(uri)
        if not self._is_in_basedir(path):
            logger.debug("Ignoring path outside playlist dir: %s", uri)
            return False
        try:
            self._abspath(path).unlink()
        except OSError as e:
            log_environment_error(f"Error deleting playlist {uri!r}", e)
            return False
        else:
            return True

    # Retrieve items in a playlist identified by its URI
    def get_items(self, uri: Uri) -> list[Ref] | None:
        # Logic to retrieve items in a playlist with error handling
        path = translator.uri_to_path(uri)
        if not self._is_in_basedir(path):
            logger.debug("Ignoring path outside playlist dir: %s", uri)
            return None
        try:
            with self._open(path, "r") as fp:
                items = translator.load_items(fp, self._base_dir)
        except OSError as e:
            log_environment_error(f"Error reading playlist {uri!r}", e)
        else:
            return items

    # Lookup details of a playlist identified by its URI
    def lookup(self, uri: Uri) -> Playlist | None:
        # Logic to look up details of a playlist with error handling
        path = translator.uri_to_path(uri)
        if not self._is_in_basedir(path):
            logger.debug("Ignoring path outside playlist dir: %s", uri)
            return None
        try:
            with self._open(path, "r") as fp:
                items = translator.load_items(fp, self._base_dir)
            mtime = self._abspath(path).stat().st_mtime
        except OSError as e:
            log_environment_error(f"Error reading playlist {uri!r}", e)
        else:
            return translator.playlist(path, items, mtime)

    # Refresh the playlist provider
    def refresh(self) -> None:
        pass  # nothing to do

    # Save the playlist details
    def save(self, playlist: Playlist) -> Playlist | None:
        # Logic to save playlist details with error handling
        path = translator.uri_to_path(playlist.uri)
        if not self._is_in_basedir(path):
            logger.debug("Ignoring path outside playlist dir: %s", playlist.uri)
            return None
        name = translator.name_from_path(path)
        try:
            with self._open(path, "w") as fp:
                translator.dump_items(playlist.tracks, fp)
            if playlist.name and playlist.name != name:
                orig_path = path
                path = translator.path_from_name(playlist.name.strip())
                path = path.with_suffix(orig_path.suffix)
                self._abspath(orig_path).rename(self._abspath(path))
            mtime = self._abspath(path).stat().st_mtime
        except OSError as e:
            log_environment_error(f"Error saving playlist {playlist.uri!r}", e)
        else:
            return translator.playlist(path, playlist.tracks, mtime)

    # Helper method to convert a relative path to an absolute path
    def _abspath(self, path: Path) -> Path:
        # Logic to convert a relative path to an absolute path
        if path.is_absolute():
            return path
        return self._playlists_dir / path

    # Check if a given local path is within the base directory
    def _is_in_basedir(self, local_path: Path) -> bool:
        # Logic to check if a path is within the base directory
        local_path = self._abspath(local_path)
        return path.is_path_inside_base_dir(local_path, self._playlists_dir)

    # Open a file identified by its path with specified mode and encoding
    def _open(
        self, path: Path, mode: str = "r"
    ) -> contextlib._GeneratorContextManager[IO[Any]] | IO[Any]:
        # Logic to open a file with specified mode and encoding
        encoding = "utf-8" if path.suffix == ".m3u8" else self._default_encoding
        
        # Ensure the path is inside the playlist directory
        if not path.is_absolute():
            path = self._abspath(path)
        if not self._is_in_basedir(path):
            raise BackendError(
                f"Path {path!r} is not inside playlist dir {self._playlists_dir!r}"
            )
            
        # Return a context manager to replace the file contents atomically
        if "w" in mode:
            return replace(path, mode, encoding=encoding, errors="replace")
        return path.open(mode, encoding=encoding, errors="replace")
