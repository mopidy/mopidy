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


def _get_obj(name):
    logger.debug('Loading: %s', name)
    if '.' not in name:
        raise ImportError("Couldn't load: %s" % name)
    module_name = name[:name.rindex('.')]
    obj_name = name[name.rindex('.') + 1:]
    try:
        module = import_module(module_name)
        obj = getattr(module, obj_name)
    except (ImportError, AttributeError):
        raise ImportError("Couldn't load: %s" % name)
    return obj


# We provide both get_class and get_function to make it more obvious what the
# intent of our code really is.
get_class = _get_obj
get_function = _get_obj


def locale_decode(bytestr):
    try:
        return unicode(bytestr)
    except UnicodeError:
        return str(bytestr).decode(locale.getpreferredencoding())
