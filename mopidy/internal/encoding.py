from __future__ import absolute_import, unicode_literals

import locale

from mopidy import compat


def locale_decode(value):
    if isinstance(value, compat.text_type):
        return value

    if not isinstance(value, bytes):
        if compat.PY2:
            value = bytes(value)
        else:
            value = compat.text_type(value).encode()

    try:
        return value.decode()
    except UnicodeDecodeError:
        return value.decode(locale.getpreferredencoding(), 'replace')
