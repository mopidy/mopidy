import logging
import os
import sys
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
