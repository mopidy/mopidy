import logging
import os
import sys
import re
import urllib

logger = logging.getLogger('mopidy.utils.path')

def get_or_create_folder(folder):
    folder = os.path.expanduser(folder)
    if os.path.isfile(folder):
        raise OSError('A file with the same name as the desired ' \
            'dir, "%s", already exists.' % folder)
    elif not os.path.isdir(folder):
        logger.info(u'Creating dir %s', folder)
        os.makedirs(folder, 0755)
    return folder

def get_or_create_file(filename):
    filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
        logger.info(u'Creating file %s', filename)
        open(filename, 'w')
    return filename

def path_to_uri(*paths):
    path = os.path.join(*paths)
    path = path.encode('utf-8')
    if sys.platform == 'win32':
        return 'file:' + urllib.pathname2url(path)
    return 'file://' + urllib.pathname2url(path)

def uri_to_path(uri):
    if sys.platform == 'win32':
        path = urllib.url2pathname(re.sub('^file:', '', uri))
    else:
        path = urllib.url2pathname(re.sub('^file://', '', uri))
    return path.encode('latin1').decode('utf-8') # Undo double encoding

def split_path(path):
    parts = []
    while True:
        path, part = os.path.split(path)
        if part:
            parts.insert(0, part)
        if not path or path == '/':
            break
    return parts

# pylint: disable = W0612
# Unused variable 'dirnames'
def find_files(path):
    if os.path.isfile(path):
        if not isinstance(path, unicode):
            path = path.decode('utf-8')
        yield path
    else:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filename = os.path.join(dirpath, filename)
                if not isinstance(filename, unicode):
                    filename = filename.decode('utf-8')
                yield filename
# pylint: enable = W0612

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
