from __future__ import unicode_literals

from mopidy import exceptions
from mopidy.config import types


def _did_you_mean(name, choices):
    """Suggest most likely setting based on levenshtein."""
    if not choices:
        return None

    name = name.lower()
    candidates = [(_levenshtein(name, c), c) for c in choices]
    candidates.sort()

    if candidates[0][0] <= 3:
        return candidates[0][1]
    return None


def _levenshtein(a, b):
    """Calculates the Levenshtein distance between a and b."""
    n, m = len(a), len(b)
    if n > m:
        return _levenshtein(b, a)

    current = xrange(n + 1)
    for i in xrange(1, m + 1):
        previous, current = current, [i] + [0] * n
        for j in xrange(1, n + 1):
            add, delete = previous[j] + 1, current[j - 1] + 1
            change = previous[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current[j] = min(add, delete, change)
    return current[n]


class ConfigSchema(object):
    """Logical group of config values that correspond to a config section.

    Schemas are set up by assigning config keys with config values to
    instances.  Once setup :meth:`convert` can be called with a list of
    ``(key, value)`` tuples to process. For convienience we also support
    :meth:`format` method that can used for printing out the converted values.
    """
    # TODO: Use collections.OrderedDict once 2.6 support is gone (#344)
    def __init__(self, name):
        self.name = name
        self._schema = {}
        self._order = []

    def __setitem__(self, key, value):
        if key not in self._schema:
            self._order.append(key)
        self._schema[key] = value

    def __getitem__(self, key):
        return self._schema[key]

    def format(self, values):
        # TODO: should the output be encoded utf-8 since we use that in
        # serialize for strings?
        lines = ['[%s]' % self.name]
        for key in self._order:
            value = values.get(key)
            if value is not None:
                lines.append('%s = %s' % (
                    key, self._schema[key].format(value)))
        return '\n'.join(lines)

    def convert(self, items):
        errors = {}
        values = {}

        for key, value in items:
            try:
                values[key] = self._schema[key].deserialize(value)
            except KeyError:  # not in our schema
                errors[key] = 'unknown config key.'
                suggestion = _did_you_mean(key, self._schema.keys())
                if suggestion:
                    errors[key] += ' Did you mean %s?' % suggestion
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

    Ensures that ``enabled`` config value is present.
    """
    def __init__(self, name):
        super(ExtensionConfigSchema, self).__init__(name)
        self['enabled'] = types.Boolean()


class LogLevelConfigSchema(object):
    """Special cased schema for handling a config section with loglevels.

    Expects the config keys to be logger names and the values to be log levels
    as understood by the :class:`LogLevel` config value. Does not sub-class
    :class:`ConfigSchema`, but implements the same interface.
    """
    def __init__(self, name):
        self.name = name
        self._config_value = types.LogLevel()

    def format(self, values):
        lines = ['[%s]' % self.name]
        for key, value in sorted(values.items()):
            if value is not None:
                lines.append('%s = %s' % (
                    key, self._config_value.format(value)))
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
