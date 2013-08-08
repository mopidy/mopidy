from __future__ import unicode_literals

import os


def path_to_data_dir(name):
    if not isinstance(name, bytes):
        name = name.encode('utf-8')
    path = os.path.dirname(__file__)
    path = os.path.join(path, b'data')
    path = os.path.abspath(path)
    return os.path.join(path, name)


class IsA(object):
    def __init__(self, klass):
        self.klass = klass

    def __eq__(self, rhs):
        try:
            return isinstance(rhs, self.klass)
        except TypeError:
            return type(rhs) == type(self.klass)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return str(self.klass)


any_int = IsA(int)
any_str = IsA(str)
any_unicode = IsA(unicode)
