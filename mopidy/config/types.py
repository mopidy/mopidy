from __future__ import unicode_literals

import logging
import re
import socket

from mopidy.utils import path
from mopidy.config import validators


def decode(value):
    if isinstance(value, unicode):
        return value
    # TODO: only unescape \n \t and \\?
    return value.decode('string-escape').decode('utf-8')


def encode(value):
    if not isinstance(value, unicode):
        return value
    for char in ('\\', '\n', '\t'):  # TODO: more escapes?
        value = value.replace(char, char.encode('unicode-escape'))
    return value.encode('utf-8')


class ConfigValue(object):
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

    choices = None
    """
    Collection of valid choices for converted value. Must be combined with
    :func:`~mopidy.config.validators.validate_choice` in :meth:`deserialize`
    do any thing.
    """

    minimum = None
    """
    Minimum of converted value. Must be combined with
    :func:`~mopidy.config.validators.validate_minimum` in :meth:`deserialize`
    do any thing.
    """

    maximum = None
    """
    Maximum of converted value. Must be combined with
    :func:`~mopidy.config.validators.validate_maximum` in :meth:`deserialize`
    do any thing.
    """

    optional = None
    """Indicate if this field is required."""

    secret = None
    """Indicate if we should mask the when printing for human consumption."""

    def __init__(self, **kwargs):
        self.choices = kwargs.get('choices')
        self.minimum = kwargs.get('minimum')
        self.maximum = kwargs.get('maximum')
        self.optional = kwargs.get('optional')
        self.secret = kwargs.get('secret')

    def deserialize(self, value):
        """Cast raw string to appropriate type."""
        return value

    def serialize(self, value):
        """Convert value back to string for saving."""
        return str(value)

    def format(self, value):
        """Format value for display."""
        if self.secret and value is not None:
            return '********'
        return self.serialize(value)


class String(ConfigValue):
    """String value

    Supported kwargs: ``optional``, ``choices``, and ``secret``.
    """
    def deserialize(self, value):
        value = decode(value).strip()
        validators.validate_required(value, not self.optional)
        validators.validate_choice(value, self.choices)
        if not value:
            return None
        return value

    def serialize(self, value):
        return encode(value)


class Integer(ConfigValue):
    """Integer value

    Supported kwargs: ``choices``, ``minimum``, ``maximum``, and ``secret``
    """
    def deserialize(self, value):
        value = int(value)
        validators.validate_choice(value, self.choices)
        validators.validate_minimum(value, self.minimum)
        validators.validate_maximum(value, self.maximum)
        return value


class Boolean(ConfigValue):
    """Boolean value

    Accepts ``1``, ``yes``, ``true``, and ``on`` with any casing as
    :class:`True`.

    Accepts ``0``, ``no``, ``false``, and ``off`` with any casing as
    :class:`False`.

    Supported kwargs: ``secret``
    """
    true_values = ('1', 'yes', 'true', 'on')
    false_values = ('0', 'no', 'false', 'off')

    def deserialize(self, value):
        if value.lower() in self.true_values:
            return True
        elif value.lower() in self.false_values:
            return False

        raise ValueError('invalid value for boolean: %r' % value)

    def serialize(self, value):
        if value:
            return 'true'
        else:
            return 'false'


class List(ConfigValue):
    """List value

    Supports elements split by commas or newlines.

    Supported kwargs: ``optional`` and ``secret``
    """
    def deserialize(self, value):
        validators.validate_required(value, not self.optional)
        if '\n' in value:
            values = re.split(r'\s*\n\s*', value.strip())
        else:
            values = re.split(r'\s*,\s*', value.strip())
        return tuple([v for v in values if v])

    def serialize(self, value):
        return '\n  ' + '\n  '.join(v.encode('utf-8') for v in value)


class LogLevel(ConfigValue):
    """Log level value

    Expects one of ``critical``, ``error``, ``warning``, ``info``, ``debug``
    with any casing.

    Supported kwargs: ``secret``
    """
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }

    def deserialize(self, value):
        validators.validate_choice(value.lower(), self.levels.keys())
        return self.levels.get(value.lower())

    def serialize(self, value):
        return dict((v, k) for k, v in self.levels.items()).get(value)


class Hostname(ConfigValue):
    """Hostname value

    Supported kwargs: ``optional`` and ``secret``
    """
    def deserialize(self, value):
        validators.validate_required(value, not self.optional)
        if not value.strip():
            return None
        try:
            socket.getaddrinfo(value, None)
        except socket.error:
            raise ValueError('must be a resolveable hostname or valid IP')
        return value


class Port(Integer):
    """Port value

    Expects integer in the range 1-65535

    Supported kwargs: ``choices`` and ``secret``
    """
    # TODO: consider probing if port is free or not?
    def __init__(self, **kwargs):
        super(Port, self).__init__(**kwargs)
        self.minimum = 1
        self.maximum = 2 ** 16 - 1


class ExpandedPath(bytes):
    def __new__(self, value):
        expanded = path.expand_path(value)
        return super(ExpandedPath, self).__new__(self, expanded)

    def __init__(self, value):
        self.original = value


class Path(ConfigValue):
    """File system path

    The following expansions of the path will be done:

    - ``~`` to the current user's home directory

    - ``$XDG_CACHE_DIR`` according to the XDG spec

    - ``$XDG_CONFIG_DIR`` according to the XDG spec

    - ``$XDG_DATA_DIR`` according to the XDG spec

    - ``$XDG_MUSIC_DIR`` according to the XDG spec

    Supported kwargs: ``optional``, ``choices``, and ``secret``
    """
    def deserialize(self, value):
        value = value.strip()
        validators.validate_required(value, not self.optional)
        validators.validate_choice(value, self.choices)
        if not value:
            return None
        return ExpandedPath(value)

    def serialize(self, value):
        if isinstance(value, ExpandedPath):
            return value.original
        return value
