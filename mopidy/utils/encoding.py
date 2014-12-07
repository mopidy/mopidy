from __future__ import absolute_import, unicode_literals

import locale

from mopidy import compat


def locale_decode(bytestr):
    try:
        return compat.text_type(bytestr)
    except UnicodeError:
        return bytes(bytestr).decode(locale.getpreferredencoding())
