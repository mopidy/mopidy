import logging
import pathlib
import re
import urllib.parse
from os import PathLike
from typing import Literal

from platformdirs import PlatformDirs

from mopidy.types import Uri

logger = logging.getLogger(__name__)


def get_xdg_dirs() -> dict[str, pathlib.Path]:
    """Returns a dict of all the known XDG Base Directories for the current user.

    The base and user directories are always available. On Unix, user directory
    overrides are read from `$XDG_CONFIG_HOME/user-dirs.dirs`.

    See https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    for the XDG Base Directory specification.
    """
    dirs = PlatformDirs()
    return {
        "XDG_CACHE_DIR": dirs.user_cache_path,
        "XDG_CONFIG_DIR": dirs.user_config_path,
        "XDG_DATA_DIR": dirs.user_data_path,
        "XDG_DESKTOP_DIR": dirs.user_desktop_path,
        "XDG_DOWNLOAD_DIR": dirs.user_downloads_path,
        "XDG_DOCUMENTS_DIR": dirs.user_documents_path,
        "XDG_MUSIC_DIR": dirs.user_music_path,
        "XDG_PICTURES_DIR": dirs.user_pictures_path,
        "XDG_VIDEOS_DIR": dirs.user_videos_path,
    }


def get_or_create_dir(dir_path: str | PathLike[str]) -> pathlib.Path:
    dir_path = expand_path(dir_path)
    if dir_path.is_file():
        msg = (
            f"A file with the same name as the desired dir, "
            f"{dir_path!r}, already exists."
        )
        raise OSError(msg)
    if not dir_path.is_dir():
        logger.info(f"Creating dir {dir_path.as_uri()}")
        dir_path.mkdir(mode=0o755, parents=True)
    return dir_path


def get_or_create_file(
    file_path: str | PathLike[str],
    mkdir: bool = True,
    content: bytes | str | None = None,
    errors: Literal["strict", "ignore", "surrogateescape"] = "strict",
) -> pathlib.Path:
    file_path = expand_path(file_path)
    if file_path.is_file():
        return file_path
    if mkdir:
        get_or_create_dir(file_path.parent)
    logger.info(f"Creating file {file_path.as_uri()}")
    file_path.touch(exist_ok=False)
    match content:
        case str():
            file_path.write_text(content, errors=errors)
        case bytes():
            file_path.write_bytes(content)
        case None:
            pass
    return file_path


def get_unix_socket_path(socket_path: str) -> pathlib.Path | None:
    match = re.search("^unix:(.*)", socket_path)
    if not match:
        return None
    return pathlib.Path(match.group(1))


def path_to_uri(path: str | PathLike[str]) -> Uri:
    """Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that [uri_to_path][] can return the same
    bytestring.

    Returns a file:// URI as a unicode string.
    """
    return Uri(pathlib.Path(path).as_uri())


def uri_to_path(uri: Uri | str) -> pathlib.Path:
    """Convert an URI to a OS specific path."""
    bytes_path = urllib.parse.unquote_to_bytes(urllib.parse.urlsplit(uri).path)
    unicode_path = bytes_path.decode(errors="surrogateescape")
    return pathlib.Path(unicode_path)


XDG_DIRS = get_xdg_dirs()


def expand_path(path: bytes | str | PathLike[str]) -> pathlib.Path:
    if isinstance(path, bytes):
        path = path.decode(errors="surrogateescape")
    path = str(pathlib.Path(path))  # pyright: ignore[reportArgumentType,reportCallIssue]

    for xdg_var, xdg_dir in XDG_DIRS.items():
        path = path.replace("$" + xdg_var, str(xdg_dir))
    if "$" in path:
        msg = f"Unexpanded '$...' in path {path!r}"
        raise ValueError(msg)

    return pathlib.Path(path).expanduser().resolve()


def is_path_inside_base_dir(
    path: bytes | str | PathLike[str],
    base_path: bytes | str | PathLike[str],
) -> bool:
    if isinstance(path, bytes):
        path = path.decode(errors="surrogateescape")
    if isinstance(base_path, bytes):
        base_path = base_path.decode(errors="surrogateescape")

    path = pathlib.Path(path).resolve()  # pyright: ignore[reportArgumentType]
    base_path = pathlib.Path(base_path).resolve()  # pyright: ignore[reportArgumentType]

    if path.is_file():
        # Use dir of file for prefix comparison, so we don't accept
        # /tmp/foo.m3u as being inside /tmp/foo, simply because they have a
        # common prefix, /tmp/foo, which matches the base path, /tmp/foo.
        path = path.parent

    # Check if dir of file is the base path or a subdir
    try:
        path.relative_to(base_path)
    except ValueError:
        return False
    else:
        return True
