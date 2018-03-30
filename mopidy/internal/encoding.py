from __future__ import absolute_import, unicode_literals

import locale

from mopidy import compat


def locale_decode(bytestr):
    try:
        return compat.text_type(bytestr)
    except UnicodeError:
        try:
            return bytes(bytestr).decode(locale.getpreferredencoding())
        except UnicodeDecodeError:
            return bytes(bytestr).decode('UTF-8', errors='replace')
