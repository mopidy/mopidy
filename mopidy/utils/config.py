from __future__ import unicode_literals


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
