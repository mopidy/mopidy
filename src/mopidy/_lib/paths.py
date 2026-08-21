import logging
import os
import pathlib
import re
import urllib.parse
from os import PathLike
from typing import Literal

from mopidy.types import Uri

logger = logging.getLogger(__name__)

# https://cgit.freedesktop.org/xdg/xdg-user-dirs/tree/user-dirs.defaults
XDG_USER_DIR_DEFAULTS = {
    "XDG_DESKTOP_DIR": "Desktop",
    "XDG_DOWNLOAD_DIR": "Downloads",
    "XDG_TEMPLATES_DIR": "Templates",
    "XDG_PUBLICSHARE_DIR": "Public",
    "XDG_DOCUMENTS_DIR": "Documents",
    "XDG_MUSIC_DIR": "Music",
    "XDG_PICTURES_DIR": "Pictures",
    "XDG_VIDEOS_DIR": "Videos",
}

XDG_USER_DIR_NAMES = {
    name.removeprefix("XDG_").removesuffix("_DIR") for name in XDG_USER_DIR_DEFAULTS
}


def _unescape_xdg_user_dir_value(value: str) -> str:
    """Decode backslash escapes from XDG user-dir values.

    ``user-dirs.dirs`` is shell-sourceable, so quoted values may contain simple
    backslash escapes even though Mopidy intentionally does not evaluate shell.
    """
    chars: list[str] = []
    escaped = False

    for char in value:
        if escaped:
            chars.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        chars.append(char)

    if escaped:
        chars.append("\\")

    return "".join(chars)


def _parse_xdg_assignment_line(
    line: str, substitutions: dict[str, str] | None = None
) -> tuple[str, str] | None:
    """Parse a simple ``KEY=VALUE`` assignment used by XDG user-dir files.

    Both XDG helper files are line-oriented assignment files. We share the
    minimal parsing here so the file-specific helpers can stay focused on the
    rules that differ between the two formats.
    """
    key, separator, value = line.partition("=")
    if not separator:
        return None

    key = key.strip()
    value = value.strip()

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = _unescape_xdg_user_dir_value(value[1:-1])

    for old, new in (substitutions or {}).items():
        value = value.replace(old, new, 1) if value.startswith(old) else value

    return key, value


def _parse_xdg_user_dir_line(
    line: str, home: pathlib.Path
) -> tuple[str, pathlib.Path] | None:
    """Parse one ``user-dirs.dirs`` line into a resolved path.

    We accept the documented forms plus a narrow shell-sourceable subset, but
    still validate the result as either an absolute path or a ``$HOME``
    descendant before treating it as an XDG user dir.
    """
    if parsed_line := _parse_xdg_assignment_line(line, {"$HOME": str(home)}):
        key, value = parsed_line
    else:
        return None

    if key not in XDG_USER_DIR_DEFAULTS:
        return None
    if value.startswith((str(home) + "/", "/")):
        path = pathlib.Path(value).resolve()
    else:
        return None

    return key, path


def get_xdg_dirs() -> dict[str, pathlib.Path]:
    """Returns a dict of all the known XDG Base Directories for the current user.

    The keys `XDG_CACHE_DIR`, `XDG_CONFIG_DIR`, and `XDG_DATA_DIR` is
    always available.

    Additional keys, like `XDG_MUSIC_DIR`, may be available if the
    `$XDG_CONFIG_DIR/user-dirs.dirs` file exists and is parseable.

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


def _read_xdg_user_dir_defaults(
    xdg_defaults_dir: pathlib.Path,
) -> dict[str, pathlib.Path]:
    """Read defaults from ``user-dirs.defaults(5)``.

    The man page documents lines of the form ``NAME=VALUE``, where ``VALUE`` is
    a relative path from the home directory. We also tolerate surrounding
    whitespace and optional quoting so lightly hand-edited files still work,
    while keeping the stricter "relative path only" rule from the format.
    """
    defaults_file = xdg_defaults_dir / "user-dirs.defaults"
    home = pathlib.Path.home()

    result = {
        key: (home / relative_path).resolve()
        for key, relative_path in XDG_USER_DIR_DEFAULTS.items()
    }

    if not defaults_file.exists():
        return result

    for line in defaults_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if parsed_line := _parse_xdg_assignment_line(line):
            key, value = parsed_line
        else:
            continue

        if key not in XDG_USER_DIR_NAMES:
            continue
        if not value or pathlib.Path(value).is_absolute():
            continue
        result[f"XDG_{key}_DIR"] = (home / value).resolve()

    return result


def _read_xdg_user_dirs(dirs_file: pathlib.Path) -> dict[str, pathlib.Path]:
    """Read user overrides from ``user-dirs.dirs(5)``.

    The man page documents lines of the form ``XDG_NAME_DIR=VALUE``, where
    ``VALUE`` must be quoted and be either ``"$HOME/Path"`` or ``"/Path"``.
    We additionally accept a small shell-sourceable subset with surrounding
    whitespace and unquoted ``$HOME/...`` or absolute paths so we stay tolerant
    of realistic manual edits without trying to implement shell.
    """
    if not dirs_file.exists():
        return {}

    result: dict[str, pathlib.Path] = {}
    home = pathlib.Path.home()

    for line in dirs_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if parsed_line := _parse_xdg_user_dir_line(line, home):
            key, path = parsed_line
            result[key] = path

    return result


def _get_xdg_user_dirs(
    xdg_config_dir: pathlib.Path,
    xdg_defaults_dir: pathlib.Path = pathlib.Path("/etc/xdg"),
) -> dict[str, pathlib.Path]:
    """Returns XDG user dirs from builtin, system, and user defaults.

    Builtin defaults are overlaid by `$XDG_DEFAULTS_DIR/user-dirs.defaults`,
    then by `$XDG_CONFIG_HOME/user-dirs.dirs`.

    This is used at import time for most users of Mopidy. By rolling our own
    implementation instead of using `glib.get_user_special_dir` we make it
    possible for many extensions to run their test suites, which are importing
    parts of Mopidy, in a virtualenv with global site-packages disabled, and
    thus no `glib` available. The ordering mirrors the XDG tooling model so we
    can honor builtin defaults, system defaults, and user overrides without a
    runtime GLib dependency.
    """
    result = _read_xdg_user_dir_defaults(xdg_defaults_dir)
    result.update(_read_xdg_user_dirs(xdg_config_dir / "user-dirs.dirs"))
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
