import locale
import logging
import os
import sys

logger = logging.getLogger('mopidy.utils')


# TODO: user itertools.chain.from_iterable(the_list)?
def flatten(the_list):
    result = []
    for element in the_list:
        if isinstance(element, list):
            result.extend(flatten(element))
        else:
            result.append(element)
    return result


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


def locale_decode(bytestr):
    try:
        return unicode(bytestr)
    except UnicodeError:
        return str(bytestr).decode(locale.getpreferredencoding())
