import contextlib
import locale
import logging
import operator
import os
import pathlib
import tempfile

from mopidy import backend
from mopidy.internal import path

from . import Extension, translator

logger = logging.getLogger(__name__)


def log_environment_error(message, error):
    if isinstance(error.strerror, bytes):
        strerror = error.strerror.decode(locale.getpreferredencoding())
    else:
        strerror = error.strerror
    logger.error("%s: %s", message, strerror)


@contextlib.contextmanager
def replace(path, mode="w+b", encoding=None, errors=None):
    (fd, tempname) = tempfile.mkstemp(dir=str(path.parent))
    tempname = pathlib.Path(tempname)
    try:
        fp = open(fd, mode, encoding=encoding, errors=errors)
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


class M3UPlaylistsProvider(backend.PlaylistsProvider):
    def __init__(self, backend, config):
        super().__init__(backend)

        ext_config = config[Extension.ext_name]
        if ext_config["playlists_dir"] is None:
            self._playlists_dir = Extension.get_data_dir(config)
        else:
            self._playlists_dir = path.expand_path(ext_config["playlists_dir"])
        if ext_config["base_dir"] is None:
            self._base_dir = self._playlists_dir
        else:
            self._base_dir = path.expand_path(ext_config["base_dir"])
        self._default_encoding = ext_config["default_encoding"]
        self._default_extension = ext_config["default_extension"]

    def as_list(self):
        result = []
        for entry in self._playlists_dir.iterdir():
            if entry.suffix not in [".m3u", ".m3u8"]:
                continue
            elif not entry.is_file():
                continue
            else:
                playlist_path = entry.relative_to(self._playlists_dir)
                result.append(translator.path_to_ref(playlist_path))
        result.sort(key=operator.attrgetter("name"))
        return result

    def create(self, name):
        path = translator.path_from_name(name.strip(), self._default_extension)
        try:
            with self._open(path, "w"):
                pass
            mtime = self._abspath(path).stat().st_mtime
        except OSError as e:
            log_environment_error(f"Error creating playlist {name!r}", e)
        else:
            return translator.playlist(path, [], mtime)

    def delete(self, uri):
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

    def get_items(self, uri):
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

    def lookup(self, uri):
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

    def refresh(self):
        pass  # nothing to do

    def save(self, playlist):
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

    def _abspath(self, path):
        if not path.is_absolute():
            return self._playlists_dir / path
        else:
            return path

    def _is_in_basedir(self, local_path):
        local_path = self._abspath(local_path)
        return path.is_path_inside_base_dir(local_path, self._playlists_dir)

    def _open(self, path, mode="r"):
        if path.suffix == ".m3u8":
            encoding = "utf-8"
        else:
            encoding = self._default_encoding
        if not path.is_absolute():
            path = self._abspath(path)
        if not self._is_in_basedir(path):
            raise Exception(
                f"Path {path!r} is not inside playlist dir {self._playlist_dir!r}"
            )
        if "w" in mode:
            return replace(path, mode, encoding=encoding, errors="replace")
        else:
            return path.open(mode, encoding=encoding, errors="replace")
