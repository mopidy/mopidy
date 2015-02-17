from __future__ import unicode_literals

import inspect
import warnings


def _is_pykka_proxy_creation():
    return False
    stack = inspect.stack()
    try:
        calling_frame = stack[3]
    except IndexError:
        return False
    else:
        filename = calling_frame[1]
        funcname = calling_frame[3]
        return 'pykka' in filename and funcname == '_get_attributes'


def deprecated_property(
        getter=None, setter=None, message='Property is deprecated'):

    def deprecated_getter(*args):
        if not _is_pykka_proxy_creation():
            warnings.warn(message, DeprecationWarning, stacklevel=2)
        return getter(*args)

    def deprecated_setter(*args):
        if not _is_pykka_proxy_creation():
            warnings.warn(message, DeprecationWarning, stacklevel=2)
        return setter(*args)

    new_getter = getter and deprecated_getter
    new_setter = setter and deprecated_setter
    return property(new_getter, new_setter)
