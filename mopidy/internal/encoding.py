import locale


def locale_decode(value):
    if isinstance(value, str):
        return value

    if not isinstance(value, bytes):
        value = str(value).encode()

    try:
        return value.decode()
    except UnicodeDecodeError:
        return value.decode(locale.getpreferredencoding(), "replace")
