import logging
import re
import socket

from mopidy.config import validators
from mopidy.internal import log, path


def decode(value):
    if isinstance(value, bytes):
        value = value.decode(errors="surrogateescape")

    for char in ("\\", "\n", "\t"):
        value = value.replace(
            char.encode(encoding="unicode-escape").decode(), char
        )

    return value


def encode(value):
    if isinstance(value, bytes):
        value = value.decode(errors="surrogateescape")

    for char in ("\\", "\n", "\t"):
        value = value.replace(
            char, char.encode(encoding="unicode-escape").decode()
        )

    return value


class DeprecatedValue:
    pass


class ConfigValue:
    """Represents a config key's value and how to handle it.

    Normally you will only be interacting with sub-classes for config values
    that encode either deserialization behavior and/or validation.

    Each config value should be used for the following actions:

    1. Deserializing from a raw string and validating, raising ValueError on
       failure.
    2. Serializing a value back to a string that can be stored in a config.
    3. Formatting a value to a printable form (useful for masking secrets).

    :class:`None` values should not be deserialized, serialized or formatted,
    the code interacting with the config should simply skip None config values.
    """

    def deserialize(self, value):
        """Cast raw string to appropriate type."""
        return decode(value)

    def serialize(self, value, display=False):
        """Convert value back to string for saving."""
        if value is None:
            return ""
        return str(value)


class Deprecated(ConfigValue):
    """Deprecated value.

    Used for ignoring old config values that are no longer in use, but should
    not cause the config parser to crash.
    """

    def deserialize(self, value):
        return DeprecatedValue()

    def serialize(self, value, display=False):
        return DeprecatedValue()


class String(ConfigValue):
    """String value.

    Is decoded as utf-8 and \\n \\t escapes should work and be preserved.
    """

    def __init__(self, optional=False, choices=None):
        self._required = not optional
        self._choices = choices

    def deserialize(self, value):
        value = decode(value).strip()
        validators.validate_required(value, self._required)
        if not value:
            return None
        validators.validate_choice(value, self._choices)
        return value

    def serialize(self, value, display=False):
        if value is None:
            return ""
        return encode(value)


class Secret(String):
    """Secret string value.

    Is decoded as utf-8 and \\n \\t escapes should work and be preserved.

    Should be used for passwords, auth tokens etc. Will mask value when being
    displayed.
    """

    def __init__(self, optional=False, choices=None):
        self._required = not optional
        self._choices = None  # Choices doesn't make sense for secrets

    def serialize(self, value, display=False):
        if value is not None and display:
            return "********"
        return super().serialize(value, display)


class Integer(ConfigValue):
    """Integer value."""

    def __init__(
        self, minimum=None, maximum=None, choices=None, optional=False
    ):
        self._required = not optional
        self._minimum = minimum
        self._maximum = maximum
        self._choices = choices

    def deserialize(self, value):
        value = decode(value)
        validators.validate_required(value, self._required)
        if not value:
            return None
        value = int(value)
        validators.validate_choice(value, self._choices)
        validators.validate_minimum(value, self._minimum)
        validators.validate_maximum(value, self._maximum)
        return value


class Boolean(ConfigValue):
    """Boolean value.

    Accepts ``1``, ``yes``, ``true``, and ``on`` with any casing as
    :class:`True`.

    Accepts ``0``, ``no``, ``false``, and ``off`` with any casing as
    :class:`False`.
    """

    true_values = ("1", "yes", "true", "on")
    false_values = ("0", "no", "false", "off")

    def __init__(self, optional=False):
        self._required = not optional

    def deserialize(self, value):
        value = decode(value)
        validators.validate_required(value, self._required)
        if not value:
            return None
        if value.lower() in self.true_values:
            return True
        elif value.lower() in self.false_values:
            return False
        raise ValueError(f"invalid value for boolean: {value!r}")

    def serialize(self, value, display=False):
        if value is True:
            return "true"
        elif value in (False, None):
            return "false"
        else:
            raise ValueError(f"{value!r} is not a boolean")


class List(ConfigValue):
    """List value.

    Supports elements split by commas or newlines. Newlines take presedence and
    empty list items will be filtered out.
    """

    def __init__(self, optional=False):
        self._required = not optional

    def deserialize(self, value):
        value = decode(value)
        if "\n" in value:
            values = re.split(r"\s*\n\s*", value)
        else:
            values = re.split(r"\s*,\s*", value)
        values = tuple(v.strip() for v in values if v.strip())
        validators.validate_required(values, self._required)
        return tuple(values)

    def serialize(self, value, display=False):
        if not value:
            return ""
        return "\n  " + "\n  ".join(encode(v) for v in value if v)


class LogColor(ConfigValue):
    def deserialize(self, value):
        value = decode(value)
        validators.validate_choice(value.lower(), log.COLORS)
        return value.lower()

    def serialize(self, value, display=False):
        if value.lower() in log.COLORS:
            return encode(value.lower())
        return ""


class LogLevel(ConfigValue):
    """Log level value.

    Expects one of ``critical``, ``error``, ``warning``, ``info``, ``debug``,
    or ``all``, with any casing.
    """

    levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "trace": log.TRACE_LOG_LEVEL,
        "all": logging.NOTSET,
    }

    def deserialize(self, value):
        value = decode(value)
        validators.validate_choice(value.lower(), self.levels.keys())
        return self.levels.get(value.lower())

    def serialize(self, value, display=False):
        lookup = {v: k for k, v in self.levels.items()}
        if value in lookup:
            return encode(lookup[value])
        return ""


class Hostname(ConfigValue):
    """Network hostname value."""

    def __init__(self, optional=False):
        self._required = not optional

    def deserialize(self, value, display=False):
        value = decode(value).strip()
        validators.validate_required(value, self._required)
        if not value:
            return None

        socket_path = path.get_unix_socket_path(value)
        if socket_path is not None:
            path_str = Path(not self._required).deserialize(socket_path)
            return f"unix:{path_str}"

        try:
            socket.getaddrinfo(value, None)
        except OSError:
            raise ValueError("must be a resolveable hostname or valid IP")

        return value


class Port(Integer):
    """Network port value.

    Expects integer in the range 0-65535, zero tells the kernel to simply
    allocate a port for us.
    """

    def __init__(self, choices=None, optional=False):
        super().__init__(
            minimum=0, maximum=2 ** 16 - 1, choices=choices, optional=optional
        )


class _ExpandedPath(str):
    def __new__(cls, original, expanded):
        return super().__new__(cls, expanded)

    def __init__(self, original, expanded):
        self.original = original


class Path(ConfigValue):
    """File system path.

    The following expansions of the path will be done:

    - ``~`` to the current user's home directory
    - ``$XDG_CACHE_DIR`` according to the XDG spec
    - ``$XDG_CONFIG_DIR`` according to the XDG spec
    - ``$XDG_DATA_DIR`` according to the XDG spec
    - ``$XDG_MUSIC_DIR`` according to the XDG spec
    """

    def __init__(self, optional=False):
        self._required = not optional

    def deserialize(self, value):
        value = decode(value).strip()
        expanded = path.expand_path(value)
        validators.validate_required(value, self._required)
        validators.validate_required(expanded, self._required)
        if not value or expanded is None:
            return None
        return _ExpandedPath(value, expanded)

    def serialize(self, value, display=False):
        if isinstance(value, _ExpandedPath):
            value = value.original
        if isinstance(value, bytes):
            value = value.decode(errors="surrogateescape")
        return value
