import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    import ConfigParser as configparser  # noqa
    import Queue as queue  # noqa
    import thread  # noqa

    string_types = basestring
    text_type = unicode

    input = raw_input

    def itervalues(dct, **kwargs):
        return iter(dct.itervalues(**kwargs))

else:
    import configparser  # noqa
    import queue  # noqa
    import _thread as thread  # noqa

    string_types = (str,)
    text_type = str

    input = input

    def itervalues(dct, **kwargs):
        return iter(dct.values(**kwargs))
