from __future__ import unicode_literals

import logging
import re
import socket


def validate_choice(value, choices):
    """Choice validation, normally called in config value's validate()."""
    if choices is not None and value not in choices :
        names = ', '.join(repr(c) for c in choices)
        raise ValueError('%r must be one of %s.' % (value, names))


def validate_minimum(value, minimum):
    """Minimum validation, normally called in config value's validate()."""
    if minimum is not None and value < minimum:
        raise ValueError('%r must be larger than %r.' % (value, minimum))


def validate_maximum(value, maximum):
    """Maximum validation, normally called in config value's validate()."""
    if maximum is not None and value > maximum:
        raise ValueError('%r must be smaller than %r.' % (value, maximum))


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

    #: Collection of valid choices for converted value. Must be combined with
    #: :function:`validate_choices` in :method:`validate` do any thing.
    choices = None

    #: Minimum of converted value. Must be combined with
    #: :function:`validate_minimum` in :method:`validate` do any thing.
    minimum = None

    #: Maximum of converted value. Must be combined with
    #: :function:`validate_maximum` in :method:`validate` do any thing.
    maximum = None

    #: Indicate if we should mask the when printing for human consumption.
    secret = None

    def __init__(self, choices=None, minimum=None, maximum=None, secret=None):
        self.choices = choices
        self.minimum = minimum
        self.maximum = maximum
        self.secret = secret

    def deserialize(self, value):
        """Cast raw string to appropriate type."""
        return value

    def serialize(self, value):
        """Convert value back to string for saving."""
        return str(value)

    def format(self, value):
        """Format value for display."""
        if self.secret:
            return '********'
        return self.serialize(value)


class String(ConfigValue):
    def deserialize(self, value):
        value = value.strip()
        validate_choice(value, self.choices)
        return value

    def serialize(self, value):
        return value.strip()


class Integer(ConfigValue):
    def deserialize(self, value):
        value = int(value.strip())
        validate_choice(value, self.choices)
        validate_minimum(value, self.minimum)
        validate_maximum(value, self.maximum)
        return value


class Boolean(ConfigValue):
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
    def deserialize(self, value):
        if '\n' in value:
            return re.split(r'\s*\n\s*', value.strip())
        else:
            return re.split(r',\s*', value.strip())

    def serialize(self, value):
        return '\n  '.join(value)


class LogLevel(ConfigValue):
    levels = {'critical' : logging.CRITICAL,
              'error' : logging.ERROR,
              'warning' : logging.WARNING,
              'info' : logging.INFO,
              'debug' : logging.DEBUG}

    def deserialize(self, value):
        if value.lower() not in self.levels:
            raise ValueError('%r must be one of %s.' % (value, ', '.join(self.levels)))
        return self.levels.get(value.lower())

    def serialize(self, value):
        return dict((v, k) for k, v in self.levels.items()).get(value)


class Hostname(ConfigValue):
    def deserialize(self, value):
        try:
            socket.getaddrinfo(value, None)
        except socket.error:
            raise ValueError('must be a resolveable hostname or valid IP.')
        return value


class Port(Integer):
    def __init__(self, **kwargs):
        super(Port, self).__init__(**kwargs)
        self.minimum = 1
        self.maximum = 2**16 - 1
