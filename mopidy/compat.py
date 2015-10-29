from __future__ import absolute_import, unicode_literals

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
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

        urllib.parse.urlparse = py2_urlparse.urlparse
        urllib.parse.urlsplit = py2_urlparse.urlsplit
        urllib.parse.urlunsplit = py2_urlparse.urlunsplit

        return urllib

    urllib = fake_python3_urllib_module()

    string_types = basestring
    text_type = unicode

    input = raw_input

    def itervalues(dct, **kwargs):
        return iter(dct.itervalues(**kwargs))

else:
    import configparser  # noqa
    import queue  # noqa
    import _thread as thread  # noqa
    import urllib  # noqa

    string_types = (str,)
    text_type = str

    input = input

    def itervalues(dct, **kwargs):
        return iter(dct.values(**kwargs))
