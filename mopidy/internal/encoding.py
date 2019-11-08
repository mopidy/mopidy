import locale

from mopidy import compat


def locale_decode(value):
    if isinstance(value, compat.text_type):
        return value

    if not isinstance(value, bytes):
        value = compat.text_type(value).encode()

    try:
        return value.decode()
    except UnicodeDecodeError:
        return value.decode(locale.getpreferredencoding(), "replace")
