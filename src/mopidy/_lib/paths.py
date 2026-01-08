import configparser
import logging
import os
import pathlib
import re
import urllib.parse
from os import PathLike
from typing import Literal

from mopidy.types import Uri

logger = logging.getLogger(__name__)


def get_xdg_dirs() -> dict[str, pathlib.Path]:
    """Returns a dict of all the known XDG Base Directories for the current user.

    The keys ``XDG_CACHE_DIR``, ``XDG_CONFIG_DIR``, and ``XDG_DATA_DIR`` is
    always available.

    Additional keys, like ``XDG_MUSIC_DIR``, may be available if the
    ``$XDG_CONFIG_DIR/user-dirs.dirs`` file exists and is parseable.

    See https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    for the XDG Base Directory specification.
    """
    dirs = {
        "XDG_CACHE_DIR": pathlib.Path(
            os.getenv("XDG_CACHE_HOME", "~/.cache"),
        ).expanduser(),
        "XDG_CONFIG_DIR": pathlib.Path(
            os.getenv("XDG_CONFIG_HOME", "~/.config"),
        ).expanduser(),
        "XDG_DATA_DIR": pathlib.Path(
            os.getenv("XDG_DATA_HOME", "~/.local/share"),
        ).expanduser(),
    }

    dirs.update(_get_xdg_user_dirs(dirs["XDG_CONFIG_DIR"]))

    return dirs


def _get_xdg_user_dirs(xdg_config_dir: pathlib.Path) -> dict[str, pathlib.Path]:
    """Returns a dict of XDG dirs read from
    ``$XDG_CONFIG_HOME/user-dirs.dirs``.

    This is used at import time for most users of :mod:`mopidy`. By rolling our
    own implementation instead of using :meth:`glib.get_user_special_dir` we
    make it possible for many extensions to run their test suites, which are
    importing parts of :mod:`mopidy`, in a virtualenv with global site-packages
    disabled, and thus no :mod:`glib` available.
    """
    dirs_file = xdg_config_dir / "user-dirs.dirs"

    if not dirs_file.exists():
        return {}

    data = dirs_file.read_bytes()
    data = b"[XDG_USER_DIRS]\n" + data
    data = data.replace(b"$HOME", bytes(pathlib.Path.home()))
    data = data.replace(b'"', b"")

    config = configparser.RawConfigParser()
    config.read_string(data.decode())

    result: dict[str, pathlib.Path] = {}
    for k, v in config.items("XDG_USER_DIRS"):
        if v is None:  # pyright: ignore[reportUnnecessaryComparison]
            continue
        if isinstance(k, bytes):
            k = k.decode()
        result[k.upper()] = pathlib.Path(v).resolve()

    return result


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
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
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
