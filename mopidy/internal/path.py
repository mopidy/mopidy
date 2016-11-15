from __future__ import absolute_import, unicode_literals

import logging
import os
import stat
import string
import threading

from mopidy import compat, exceptions
from mopidy.compat import queue, urllib
from mopidy.internal import encoding, xdg


logger = logging.getLogger(__name__)


XDG_DIRS = xdg.get_dirs()


def get_or_create_dir(dir_path):
    if not isinstance(dir_path, bytes):
        raise ValueError('Path is not a bytestring.')
    dir_path = expand_path(dir_path)
    if os.path.isfile(dir_path):
        raise OSError(
            'A file with the same name as the desired dir, '
            '"%s", already exists.' % dir_path)
    elif not os.path.isdir(dir_path):
        logger.info('Creating dir %s', dir_path)
        os.makedirs(dir_path, 0o755)
    return dir_path


def get_or_create_file(file_path, mkdir=True, content=None):
    if not isinstance(file_path, bytes):
        raise ValueError('Path is not a bytestring.')
    file_path = expand_path(file_path)
    if isinstance(content, compat.text_type):
        content = content.encode('utf-8')
    if mkdir:
        get_or_create_dir(os.path.dirname(file_path))
    if not os.path.isfile(file_path):
        logger.info('Creating file %s', file_path)
        with open(file_path, 'wb') as fh:
            if content is not None:
                fh.write(content)
    return file_path


def path_to_uri(path):
    """
    Convert OS specific path to file:// URI.

    Accepts either unicode strings or bytestrings. The encoding of any
    bytestring will be maintained so that :func:`uri_to_path` can return the
    same bytestring.

    Returns a file:// URI as an unicode string.
    """
    if isinstance(path, compat.text_type):
        path = path.encode('utf-8')
    path = urllib.parse.quote(path)
    return urllib.parse.urlunsplit((b'file', b'', path, b'', b''))


def uri_to_path(uri):
    """
    Convert an URI to a OS specific path.

    Returns a bytestring, since the file path can contain chars with other
    encoding than UTF-8.

    If we had returned these paths as unicode strings, you wouldn't be able to
    look up the matching dir or file on your file system because the exact path
    would be lost by ignoring its encoding.
    """
    if isinstance(uri, compat.text_type):
        uri = uri.encode('utf-8')
    return urllib.parse.unquote(urllib.parse.urlsplit(uri).path)


def split_path(path):
    parts = []
    while True:
        path, part = os.path.split(path)
        if part:
            parts.insert(0, part)
        if not path or path == b'/':
            break
    return parts


def expand_path(path):
    # TODO: document as we want people to use this.
    if not isinstance(path, bytes):
        raise ValueError('Path is not a bytestring.')
    try:
        path = string.Template(path).substitute(XDG_DIRS)
    except KeyError:
        return None
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    return path


def _find_worker(relative, follow, done, work, results, errors):
    """Worker thread for collecting stat() results.

    :param str relative: directory to make results relative to
    :param bool follow: if symlinks should be followed
    :param threading.Event done: event indicating that all work has been done
    :param queue.Queue work: queue of paths to process
    :param dict results: shared dictionary for storing all the stat() results
    :param dict errors: shared dictionary for storing any per path errors
    """
    while not done.is_set():
        try:
            entry, parents = work.get(block=False)
        except queue.Empty:
            continue

        if relative:
            path = os.path.relpath(entry, relative)
        else:
            path = entry

        try:
            if follow:
                st = os.stat(entry)
            else:
                st = os.lstat(entry)

            if (st.st_dev, st.st_ino) in parents:
                errors[path] = exceptions.FindError('Sym/hardlink loop found.')
                continue

            parents = parents + [(st.st_dev, st.st_ino)]
            if stat.S_ISDIR(st.st_mode):
                for e in os.listdir(entry):
                    work.put((os.path.join(entry, e), parents))
            elif stat.S_ISREG(st.st_mode):
                results[path] = st
            elif stat.S_ISLNK(st.st_mode):
                errors[path] = exceptions.FindError('Not following symlinks.')
            else:
                errors[path] = exceptions.FindError('Not a file or directory.')

        except OSError as e:
            errors[path] = exceptions.FindError(
                encoding.locale_decode(e.strerror), e.errno)
        finally:
            work.task_done()


def _find(root, thread_count=10, relative=False, follow=False):
    """Threaded find implementation that provides stat results for files.

    Tries to protect against sym/hardlink loops by keeping an eye on parent
    (st_dev, st_ino) pairs.

    :param str root: root directory to search from, may not be a file
    :param int thread_count: number of workers to use, mainly useful to
        mitigate network lag when scanning on NFS etc.
    :param bool relative: if results should be relative to root or absolute
    :param bool follow: if symlinks should be followed
    """
    threads = []
    results = {}
    errors = {}
    done = threading.Event()
    work = queue.Queue()
    work.put((os.path.abspath(root), []))

    if not relative:
        root = None

    args = (root, follow, done, work, results, errors)
    for i in range(thread_count):
        t = threading.Thread(target=_find_worker, args=args)
        t.daemon = True
        t.start()
        threads.append(t)

    work.join()
    done.set()
    for t in threads:
        t.join()
    return results, errors


def find_mtimes(root, follow=False):
    results, errors = _find(root, relative=False, follow=follow)
    # return the mtimes as integer milliseconds
    mtimes = {f: int(st.st_mtime * 1000) for f, st in results.items()}
    return mtimes, errors


def is_path_inside_base_dir(path, base_path):
    if not isinstance(path, bytes):
        raise ValueError('path is not a bytestring')
    if not isinstance(base_path, bytes):
        raise ValueError('base_path is not a bytestring')

    if path.endswith(os.sep):
        raise ValueError('Path %s cannot end with a path separator'
                         % path)
    # Expand symlinks
    real_base_path = os.path.realpath(base_path)
    real_path = os.path.realpath(path)

    if os.path.isfile(path):
        # Use dir of file for prefix comparision, so we don't accept
        # /tmp/foo.m3u as being inside /tmp/foo, simply because they have a
        # common prefix, /tmp/foo, which matches the base path, /tmp/foo.
        real_path = os.path.dirname(real_path)

    # Check if dir of file is the base path or a subdir
    common_prefix = os.path.commonprefix([real_base_path, real_path])
    return common_prefix == real_base_path


# FIXME replace with mock usage in tests.
class Mtime(object):

    def __init__(self):
        self.fake = None

    def __call__(self, path):
        if self.fake is not None:
            return self.fake
        return int(os.stat(path).st_mtime)

    def set_fake_time(self, time):
        self.fake = time

    def undo_fake(self):
        self.fake = None


mtime = Mtime()
