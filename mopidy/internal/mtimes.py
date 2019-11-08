import pathlib
import queue
import stat
import threading

from mopidy import exceptions
from mopidy.internal import encoding


def find_mtimes(root, follow=False):
    results, errors = _find(root, relative=False, follow=follow)

    # return the mtimes as integer milliseconds
    mtimes = {f: int(st.st_mtime * 1000) for f, st in results.items()}

    return mtimes, errors


def _find(root, thread_count=10, relative=False, follow=False):
    """Threaded find implementation that provides stat results for files.

    Tries to protect against sym/hardlink loops by keeping an eye on parent
    (st_dev, st_ino) pairs.

    :param Path root: root directory to search from, may not be a file
    :param int thread_count: number of workers to use, mainly useful to
        mitigate network lag when scanning on NFS etc.
    :param bool relative: if results should be relative to root or absolute
    :param bool follow: if symlinks should be followed
    """
    root = pathlib.Path(root).resolve()
    threads = []
    results = {}
    errors = {}
    done = threading.Event()
    work = queue.Queue()
    work.put((root, []))

    if not relative:
        root = None

    args = (root, follow, done, work, results, errors)
    for _ in range(thread_count):
        t = threading.Thread(target=_find_worker, args=args)
        t.daemon = True
        t.start()
        threads.append(t)

    work.join()
    done.set()
    for t in threads:
        t.join()
    return results, errors


def _find_worker(root, follow, done, work, results, errors):
    """Worker thread for collecting stat() results.

    :param Path root: directory to make results relative to
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

        if root:
            path = entry.relative_to(root)
        else:
            path = entry

        try:
            if follow:
                st = entry.stat()
            else:
                st = entry.lstat()

            if (st.st_dev, st.st_ino) in parents:
                errors[path] = exceptions.FindError("Sym/hardlink loop found.")
                continue

            if stat.S_ISDIR(st.st_mode):
                for e in entry.iterdir():
                    work.put((e, parents + [(st.st_dev, st.st_ino)]))
            elif stat.S_ISREG(st.st_mode):
                results[path] = st
            elif stat.S_ISLNK(st.st_mode):
                errors[path] = exceptions.FindError("Not following symlinks.")
            else:
                errors[path] = exceptions.FindError("Not a file or directory.")

        except OSError as e:
            errors[path] = exceptions.FindError(
                encoding.locale_decode(e.strerror), e.errno
            )
        finally:
            work.task_done()
