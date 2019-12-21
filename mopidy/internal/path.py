import logging
import pathlib
import re
import urllib

from mopidy.internal import xdg

logger = logging.getLogger(__name__)


XDG_DIRS = xdg.get_dirs()


def get_or_create_dir(dir_path):
    dir_path = expand_path(dir_path)
    if dir_path.is_file():
        raise OSError(
            f"A file with the same name as the desired dir, "
            f"{dir_path!r}, already exists."
        )
    elif not dir_path.is_dir():
        logger.info(f"Creating dir {dir_path.as_uri()}")
        dir_path.mkdir(mode=0o755, parents=True)
    return dir_path


def get_or_create_file(file_path, mkdir=True, content=None):
    file_path = expand_path(file_path)
    if isinstance(content, str):
        content = content.encode()
    if mkdir:
        get_or_create_dir(file_path.parent)
    if not file_path.is_file():
        logger.info(f"Creating file {file_path.as_uri()}")
        file_path.touch(exist_ok=False)
        if content is not None:
            file_path.write_bytes(content)
    return file_path


def get_unix_socket_path(socket_path):
    match = re.search("^unix:(.*)", socket_path)
    if not match:
        return None
    return match.group(1)


def path_to_uri(path):
    """
    Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
    """
    return pathlib.Path(path).as_uri()


def uri_to_path(uri):
    """
    Convert an URI to a OS specific path.
    """
    bytes_path = urllib.parse.unquote_to_bytes(urllib.parse.urlsplit(uri).path)
    unicode_path = bytes_path.decode(errors="surrogateescape")
    return pathlib.Path(unicode_path)


def expand_path(path):
    if isinstance(path, bytes):
        path = path.decode(errors="surrogateescape")
    path = str(pathlib.Path(path))

    for xdg_var, xdg_dir in XDG_DIRS.items():
        path = path.replace("$" + xdg_var, str(xdg_dir))
    if "$" in path:
        return None

    return pathlib.Path(path).expanduser().resolve()


def is_path_inside_base_dir(path, base_path):
    if isinstance(path, bytes):
        path = path.decode(errors="surrogateescape")
    if isinstance(base_path, bytes):
        base_path = base_path.decode(errors="surrogateescape")

    path = pathlib.Path(path).resolve()
    base_path = pathlib.Path(base_path).resolve()

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
