import logging
import os
import sys
import urllib

logger = logging.getLogger('mopidy.utils.path')

def get_or_create_folder(folder):
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        logger.info(u'Creating %s', folder)
        os.mkdir(folder, 0755)
    return folder

def path_to_uri(*paths):
    path = os.path.join(*paths)
    #path = os.path.expanduser(path) # FIXME Waiting for test case?
    path = path.encode('utf-8')
    if sys.platform == 'win32':
        return 'file:' + urllib.pathname2url(path)
    return 'file://' + urllib.pathname2url(path)
