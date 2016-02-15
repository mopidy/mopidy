from __future__ import absolute_import, unicode_literals

import os

from mopidy import compat


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
            return type(rhs) == type(self.klass)  # flake8: noqa

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return str(self.klass)


any_int = IsA(compat.integer_types)
any_str = IsA(compat.string_types)
any_unicode = IsA(compat.text_type)
