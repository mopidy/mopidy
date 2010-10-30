import logging
import os
import sys
import re
import urllib

logger = logging.getLogger('mopidy.utils.path')

def get_or_create_folder(folder):
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        logger.info(u'Creating dir %s', folder)
        os.mkdir(folder, 0755)
    return folder

def get_or_create_file(filename):
    filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
        logger.info(u'Creating file %s', filename)
        open(filename, 'w')
    return filename

def path_to_uri(*paths):
    path = os.path.join(*paths)
    #path = os.path.expanduser(path) # FIXME Waiting for test case?
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

def find_files(path):
    path = os.path.expanduser(path)
    if os.path.isfile(path):
        filename = os.path.abspath(path)
        if not isinstance(filename, unicode):
            filename = filename.decode('utf-8')
        yield filename
    else:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                dirpath = os.path.abspath(dirpath)
                filename = os.path.join(dirpath, filename)
                if not isinstance(filename, unicode):
                    filename = filename.decode('utf-8')
                yield filename

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
