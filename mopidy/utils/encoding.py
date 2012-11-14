from __future__ import unicode_literals

import locale


def locale_decode(bytestr):
    try:
        return unicode(bytestr)
    except UnicodeError:
        return str(bytestr).decode(locale.getpreferredencoding())
