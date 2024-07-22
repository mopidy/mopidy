import logging
import pathlib
import re
import urllib.parse
from os import PathLike
from typing import AnyStr

from mopidy.internal import xdg
from mopidy.types import Uri

logger = logging.getLogger(__name__)


XDG_DIRS = xdg.get_dirs()


def get_or_create_dir(dir_path: str | PathLike[str]) -> pathlib.Path:
    dir_path = expand_path(dir_path)
    if dir_path.is_file():
        raise OSError(
            f"A file with the same name as the desired dir, "
            f"{dir_path!r}, already exists."
        )
    if not dir_path.is_dir():
        logger.info(f"Creating dir {dir_path.as_uri()}")
        dir_path.mkdir(mode=0o755, parents=True)
    return dir_path


def get_or_create_file(
    file_path: str | PathLike[str],
    mkdir: bool = True,
    content: AnyStr | None = None,
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
            file_path.write_text(content)
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
    """
    Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
    """
    return Uri(pathlib.Path(path).as_uri())


def uri_to_path(uri: Uri | str) -> pathlib.Path:
    """
    Convert an URI to a OS specific path.
    """
    bytes_path = urllib.parse.unquote_to_bytes(urllib.parse.urlsplit(uri).path)
    unicode_path = bytes_path.decode(errors="surrogateescape")
    return pathlib.Path(unicode_path)


def expand_path(path: bytes | str | PathLike[str]) -> pathlib.Path:
    if isinstance(path, bytes):
        path = path.decode(errors="surrogateescape")
    path = str(pathlib.Path(path))  # pyright: ignore[reportArgumentType,reportCallIssue]

    for xdg_var, xdg_dir in XDG_DIRS.items():
        path = path.replace("$" + xdg_var, str(xdg_dir))
    if "$" in path:
        raise ValueError(f"Unexpanded '$...' in path {path!r}")

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
        # Use dir of file for prefix comparision, so we don't accept
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
