from __future__ import absolute_import, unicode_literals

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    import collections as collections_abc  # noqa
    import ConfigParser as configparser  # noqa
    import Queue as queue  # noqa
    import thread  # noqa

    def fake_python3_urllib_module():
        import types
        import urllib as py2_urllib
        import urlparse as py2_urlparse

        urllib = types.ModuleType(b'urllib')  # noqa
        urllib.parse = types.ModuleType(b'urlib.parse')

        urllib.parse.quote = py2_urllib.quote
        urllib.parse.unquote = py2_urllib.unquote

        urllib.parse.urljoin = py2_urlparse.urljoin
        urllib.parse.urlparse = py2_urlparse.urlparse
        urllib.parse.urlsplit = py2_urlparse.urlsplit
        urllib.parse.urlunsplit = py2_urlparse.urlunsplit

        return urllib

    urllib = fake_python3_urllib_module()

    integer_types = (int, long)  # noqa
    string_types = basestring  # noqa
    text_type = unicode  # noqa

    input = raw_input  # noqa
    intern = intern  # noqa

    def itervalues(dct, **kwargs):
        return iter(dct.itervalues(**kwargs))

    from inspect import getargspec  # noqa
    from itertools import izip_longest as zip_longest  # noqa

else:
    import collections.abc as collections_abc  # noqa
    import configparser  # noqa
    import queue  # noqa
    import _thread as thread  # noqa
    import urllib  # noqa

    integer_types = (int,)
    string_types = (str,)
    text_type = str

    input = input
    intern = sys.intern

    def itervalues(dct, **kwargs):
        return iter(dct.values(**kwargs))

    from itertools import zip_longest  # noqa

    import inspect  # noqa

    def getargspec(func):
        spec = inspect.getfullargspec(func)
        return inspect.ArgSpec(
            spec.args, spec.varargs, spec.varkw, spec.defaults)


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        if hasattr(cls, '__qualname__'):
            orig_vars['__qualname__'] = cls.__qualname__
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper
