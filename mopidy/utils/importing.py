from __future__ import unicode_literals

import logging
import sys


logger = logging.getLogger('mopidy.utils')


def import_module(name):
    __import__(name)
    return sys.modules[name]


def get_class(name):
    logger.debug('Loading: %s', name)
    if '.' not in name:
        raise ImportError("Couldn't load: %s" % name)
    module_name = name[:name.rindex('.')]
    cls_name = name[name.rindex('.') + 1:]
    try:
        module = import_module(module_name)
        cls = getattr(module, cls_name)
    except (ImportError, AttributeError):
        raise ImportError("Couldn't load: %s" % name)
    return cls
