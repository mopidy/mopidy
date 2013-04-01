from __future__ import unicode_literals

import logging
import re
import socket

from mopidy import exceptions


def validate_required(value, required):
    """Required validation, normally called in config value's validate() on the
    raw string, _not_ the converted value."""
    if required and not value.strip():
        raise ValueError('must be set.')


def validate_choice(value, choices):
    """Choice validation, normally called in config value's validate()."""
    if choices is not None and value not in choices:
        names = ', '.join(repr(c) for c in choices)
        raise ValueError('must be one of %s, not %s.' % (names, value))


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

    #: Indicate if this field is required.
    optional = None

    #: Indicate if we should mask the when printing for human consumption.
    secret = None

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
    """String values.

    Supports: optional choices and secret.
    """
    def deserialize(self, value):
        value = value.strip()
        validate_required(value, not self.optional)
        validate_choice(value, self.choices)
        if not value:
            return None
        return value

    def serialize(self, value):
        return value.encode('utf-8')


class Integer(ConfigValue):
    """Integer values.

    Supports: choices, minimum, maximum and secret.
    """
    def deserialize(self, value):
        value = int(value)
        validate_choice(value, self.choices)
        validate_minimum(value, self.minimum)
        validate_maximum(value, self.maximum)
        return value


class Boolean(ConfigValue):
    """Boolean values.

    Supports: secret.
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
    """List values split by comma or newline.

    Supports: optional and secret.
    """
    def deserialize(self, value):
        validate_required(value, not self.optional)
        if '\n' in value:
            values = re.split(r'\s*\n\s*', value.strip())
        else:
            values = re.split(r'\s*,\s*', value.strip())
        return [v for v in values if v]

    def serialize(self, value):
        return '\n  '.join(v.encode('utf-8') for v in value)


class LogLevel(ConfigValue):
    """Log level values.

    Supports: secret.
    """
    levels = {'critical' : logging.CRITICAL,
              'error' : logging.ERROR,
              'warning' : logging.WARNING,
              'info' : logging.INFO,
              'debug' : logging.DEBUG}

    def deserialize(self, value):
        validate_choice(value.lower(), self.levels.keys())
        return self.levels.get(value.lower())

    def serialize(self, value):
        return dict((v, k) for k, v in self.levels.items()).get(value)


class Hostname(ConfigValue):
    """Hostname values.

    Supports: optional and secret.
    """
    def deserialize(self, value):
        validate_required(value, not self.optional)
        if not value.strip():
            return None
        try:
            socket.getaddrinfo(value, None)
        except socket.error:
            raise ValueError('must be a resolveable hostname or valid IP')
        return value


class Port(Integer):
    """Port values limited to 1-65535.

    Supports: choices and secret.
    """
    # TODO: consider probing if port is free or not?
    def __init__(self, **kwargs):
        super(Port, self).__init__(**kwargs)
        self.minimum = 1
        self.maximum = 2**16 - 1


class ConfigSchema(object):
    """Logical group of config values that correspond to a config section.

    Schemas are set up by assigning config keys with config values to instances.
    Once setup :meth:`convert` can be called with a list of `(key, value)` tuples to
    process. For convienience we also support :meth:`format` method that can used
    for printing out the converted values.
    """
    # TODO: Use collections.OrderedDict once 2.6 support is gone (#344)
    def __init__(self):
        self._schema = {}
        self._order = []

    def __setitem__(self, key, value):
        if key not in self._schema:
            self._order.append(key)
        self._schema[key] = value

    def __getitem__(self, key):
        return self._schema[key]

    def format(self, name, values):
        lines = ['[%s]' % name]
        for key in self._order:
            value = values.get(key)
            if value is not None:
                lines.append('%s = %s' % (key, self._schema[key].format(value)))
        return '\n'.join(lines)

    def convert(self, items):
        errors = {}
        values = {}

        for key, value in items:
            try:
                values[key] = self._schema[key].deserialize(value)
            except KeyError:  # not in our schema
                errors[key] = 'unknown config key.'
            except ValueError as e:  # deserialization failed
                errors[key] = str(e)

        for key in self._schema:
            if key not in values and key not in errors:
                errors[key] = 'config key not found.'

        if errors:
            raise exceptions.ConfigError(errors)
        return values


class ExtensionConfigSchema(ConfigSchema):
    """Sub-classed :class:`ConfigSchema` for use in extensions.

    Ensures that `enabled` config value is present and that section name is
    prefixed with ext.
    """
    def __init__(self):
        super(ExtensionConfigSchema, self).__init__()
        self['enabled'] = Boolean()

    def format(self, name, values):
        return super(ExtensionConfigSchema, self).format('ext.%s' % name, values)


class LogLevelConfigSchema(object):
    """Special cased schema for handling a config section with loglevels.

    Expects the config keys to be logger names and the values to be log levels
    as understood by the :class:`LogLevel` config value. Does not sub-class
    :class:`ConfigSchema`, but implements the same interface.
    """
    def __init__(self):
        self._config_value = LogLevel()

    def format(self, name, values):
        lines = ['[%s]' % name]
        for key, value in sorted(values.items()):
            if value is not None:
                lines.append('%s = %s' % (key, self._config_value.format(value)))
        return '\n'.join(lines)

    def convert(self, items):
        errors = {}
        values = {}

        for key, value in items:
            try:
                if value.strip():
                    values[key] = self._config_value.deserialize(value)
            except ValueError as e:  # deserialization failed
                errors[key] = str(e)

        if errors:
            raise exceptions.ConfigError(errors)
        return values
