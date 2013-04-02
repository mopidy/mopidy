from __future__ import unicode_literals

import logging
import mock
import socket

from mopidy import exceptions
from mopidy.utils import config

from tests import unittest


class ValidateChoiceTest(unittest.TestCase):
    def test_no_choices_passes(self):
        config.validate_choice('foo', None)

    def test_valid_value_passes(self):
        config.validate_choice('foo', ['foo', 'bar', 'baz'])
        config.validate_choice(1, [1, 2, 3])

    def test_empty_choices_fails(self):
        self.assertRaises(ValueError, config.validate_choice, 'foo', [])

    def test_invalid_value_fails(self):
        words = ['foo', 'bar', 'baz']
        self.assertRaises(ValueError, config.validate_choice, 'foobar', words)
        self.assertRaises(ValueError, config.validate_choice, 5, [1, 2, 3])


class ValidateMinimumTest(unittest.TestCase):
    def test_no_minimum_passes(self):
        config.validate_minimum(10, None)

    def test_valid_value_passes(self):
        config.validate_minimum(10, 5)

    def test_to_small_value_fails(self):
        self.assertRaises(ValueError, config.validate_minimum, 10, 20)

    def test_to_small_value_fails_with_zero_as_minimum(self):
        self.assertRaises(ValueError, config.validate_minimum, -1, 0)


class ValidateMaximumTest(unittest.TestCase):
    def test_no_maximum_passes(self):
        config.validate_maximum(5, None)

    def test_valid_value_passes(self):
        config.validate_maximum(5, 10)

    def test_to_large_value_fails(self):
        self.assertRaises(ValueError, config.validate_maximum, 10, 5)

    def test_to_large_value_fails_with_zero_as_maximum(self):
        self.assertRaises(ValueError, config.validate_maximum, 5, 0)


class ValidateRequiredTest(unittest.TestCase):
    def test_passes_when_false(self):
        config.validate_required('foo', False)
        config.validate_required('', False)
        config.validate_required('  ', False)

    def test_passes_when_required_and_set(self):
        config.validate_required('foo', True)
        config.validate_required(' foo ', True)

    def test_blocks_when_required_and_emtpy(self):
        self.assertRaises(ValueError, config.validate_required, '', True)
        self.assertRaises(ValueError, config.validate_required, '  ', True)


class ConfigValueTest(unittest.TestCase):
    def test_init(self):
        value = config.ConfigValue()
        self.assertIsNone(value.choices)
        self.assertIsNone(value.maximum)
        self.assertIsNone(value.minimum)
        self.assertIsNone(value.optional)
        self.assertIsNone(value.secret)

    def test_init_with_params(self):
        kwargs = {'choices': ['foo'], 'minimum': 0, 'maximum': 10,
                  'secret': True, 'optional': True}
        value = config.ConfigValue(**kwargs)
        self.assertEqual(['foo'], value.choices)
        self.assertEqual(0, value.minimum)
        self.assertEqual(10, value.maximum)
        self.assertEqual(True, value.optional)
        self.assertEqual(True, value.secret)

    def test_deserialize_passes_through(self):
        value = config.ConfigValue()
        obj = object()
        self.assertEqual(obj, value.deserialize(obj))

    def test_serialize_conversion_to_string(self):
        value = config.ConfigValue()
        self.assertIsInstance(value.serialize(object()), basestring)

    def test_format_uses_serialize(self):
        value = config.ConfigValue()
        obj = object()
        self.assertEqual(value.serialize(obj), value.format(obj))

    def test_format_masks_secrets(self):
        value = config.ConfigValue(secret=True)
        self.assertEqual('********', value.format(object()))


class StringTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = config.String()
        self.assertEqual('foo', value.deserialize(' foo '))

    def test_deserialize_enforces_choices(self):
        value = config.String(choices=['foo', 'bar', 'baz'])
        self.assertEqual('foo', value.deserialize('foo'))
        self.assertRaises(ValueError, value.deserialize, 'foobar')

    def test_deserialize_enforces_required(self):
        value = config.String()
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_deserialize_respects_optional(self):
        value = config.String(optional=True)
        self.assertIsNone(value.deserialize(''))
        self.assertIsNone(value.deserialize(' '))

    def test_format_masks_secrets(self):
        value = config.String(secret=True)
        self.assertEqual('********', value.format('s3cret'))


class IntegerTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = config.Integer()
        self.assertEqual(123, value.deserialize('123'))
        self.assertEqual(0, value.deserialize('0'))
        self.assertEqual(-10, value.deserialize('-10'))

    def test_deserialize_conversion_failure(self):
        value = config.Integer()
        self.assertRaises(ValueError, value.deserialize, 'asd')
        self.assertRaises(ValueError, value.deserialize, '3.14')
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_deserialize_enforces_choices(self):
        value = config.Integer(choices=[1, 2, 3])
        self.assertEqual(3, value.deserialize('3'))
        self.assertRaises(ValueError, value.deserialize, '5')

    def test_deserialize_enforces_minimum(self):
        value = config.Integer(minimum=10)
        self.assertEqual(15, value.deserialize('15'))
        self.assertRaises(ValueError, value.deserialize, '5')

    def test_deserialize_enforces_maximum(self):
        value = config.Integer(maximum=10)
        self.assertEqual(5, value.deserialize('5'))
        self.assertRaises(ValueError, value.deserialize, '15')

    def test_format_masks_secrets(self):
        value = config.Integer(secret=True)
        self.assertEqual('********', value.format('1337'))


class BooleanTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = config.Boolean()
        for true in ('1', 'yes', 'true', 'on'):
            self.assertIs(value.deserialize(true), True)
            self.assertIs(value.deserialize(true.upper()), True)
            self.assertIs(value.deserialize(true.capitalize()), True)
        for false in ('0', 'no', 'false', 'off'):
            self.assertIs(value.deserialize(false), False)
            self.assertIs(value.deserialize(false.upper()), False)
            self.assertIs(value.deserialize(false.capitalize()), False)

    def test_deserialize_conversion_failure(self):
        value = config.Boolean()
        self.assertRaises(ValueError, value.deserialize, 'nope')
        self.assertRaises(ValueError, value.deserialize, 'sure')
        self.assertRaises(ValueError, value.deserialize, '')

    def test_serialize(self):
        value = config.Boolean()
        self.assertEqual('true', value.serialize(True))
        self.assertEqual('false', value.serialize(False))

    def test_format_masks_secrets(self):
        value = config.Boolean(secret=True)
        self.assertEqual('********', value.format('true'))


class ListTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = config.List()

        expected = ('foo', 'bar', 'baz')
        self.assertEqual(expected, value.deserialize('foo, bar ,baz '))

        expected = ('foo,bar', 'bar', 'baz')
        self.assertEqual(expected, value.deserialize(' foo,bar\nbar\nbaz'))

    def test_deserialize_enforces_required(self):
        value = config.List()
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_deserialize_respects_optional(self):
        value = config.List(optional=True)
        self.assertEqual(tuple(), value.deserialize(''))
        self.assertEqual(tuple(), value.deserialize(' '))

    def test_serialize(self):
        value = config.List()
        result = value.serialize(('foo', 'bar', 'baz'))
        self.assertRegexpMatches(result, r'foo\n\s*bar\n\s*baz')


class BooleanTest(unittest.TestCase):
    levels = {'critical': logging.CRITICAL,
              'error': logging.ERROR,
              'warning': logging.WARNING,
              'info': logging.INFO,
              'debug': logging.DEBUG}

    def test_deserialize_conversion_success(self):
        value = config.LogLevel()
        for name, level in self.levels.items():
            self.assertEqual(level, value.deserialize(name))
            self.assertEqual(level, value.deserialize(name.upper()))
            self.assertEqual(level, value.deserialize(name.capitalize()))

    def test_deserialize_conversion_failure(self):
        value = config.LogLevel()
        self.assertRaises(ValueError, value.deserialize, 'nope')
        self.assertRaises(ValueError, value.deserialize, 'sure')
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_serialize(self):
        value = config.LogLevel()
        for name, level in self.levels.items():
            self.assertEqual(name, value.serialize(level))
        self.assertIsNone(value.serialize(1337))


class HostnameTest(unittest.TestCase):
    @mock.patch('socket.getaddrinfo')
    def test_deserialize_conversion_success(self, getaddrinfo_mock):
        value = config.Hostname()
        value.deserialize('example.com')
        getaddrinfo_mock.assert_called_once_with('example.com', None)

    @mock.patch('socket.getaddrinfo')
    def test_deserialize_conversion_failure(self, getaddrinfo_mock):
        value = config.Hostname()
        getaddrinfo_mock.side_effect = socket.error
        self.assertRaises(ValueError, value.deserialize, 'example.com')

    @mock.patch('socket.getaddrinfo')
    def test_deserialize_enforces_required(self, getaddrinfo_mock):
        value = config.Hostname()
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')
        self.assertEqual(0, getaddrinfo_mock.call_count)

    @mock.patch('socket.getaddrinfo')
    def test_deserialize_respects_optional(self, getaddrinfo_mock):
        value = config.Hostname(optional=True)
        self.assertIsNone(value.deserialize(''))
        self.assertIsNone(value.deserialize(' '))
        self.assertEqual(0, getaddrinfo_mock.call_count)


class PortTest(unittest.TestCase):
    def test_valid_ports(self):
        value = config.Port()
        self.assertEqual(1, value.deserialize('1'))
        self.assertEqual(80, value.deserialize('80'))
        self.assertEqual(6600, value.deserialize('6600'))
        self.assertEqual(65535, value.deserialize('65535'))

    def test_invalid_ports(self):
        value = config.Port()
        self.assertRaises(ValueError, value.deserialize, '65536')
        self.assertRaises(ValueError, value.deserialize, '100000')
        self.assertRaises(ValueError, value.deserialize, '0')
        self.assertRaises(ValueError, value.deserialize, '-1')
        self.assertRaises(ValueError, value.deserialize, '')


class ConfigSchemaTest(unittest.TestCase):
    def setUp(self):
        self.schema = config.ConfigSchema()
        self.schema['foo'] = mock.Mock()
        self.schema['bar'] = mock.Mock()
        self.schema['baz'] = mock.Mock()
        self.values = {'bar': '123', 'foo': '456', 'baz': '678'}

    def test_format(self):
        self.schema['foo'].format.return_value = 'qwe'
        self.schema['bar'].format.return_value = 'asd'
        self.schema['baz'].format.return_value = 'zxc'

        expected = ['[qwerty]', 'foo = qwe', 'bar = asd', 'baz = zxc']
        result = self.schema.format('qwerty', self.values)
        self.assertEqual('\n'.join(expected), result)

    def test_format_unkwown_value(self):
        self.schema['foo'].format.return_value = 'qwe'
        self.schema['bar'].format.return_value = 'asd'
        self.schema['baz'].format.return_value = 'zxc'
        self.values['unknown'] = 'rty'

        result = self.schema.format('qwerty', self.values)
        self.assertNotIn('unknown = rty', result)

    def test_convert(self):
        self.schema.convert(self.values.items())

    def test_convert_with_missing_value(self):
        del self.values['foo']

        with self.assertRaises(exceptions.ConfigError) as cm:
            self.schema.convert(self.values.items())

        self.assertIn('not found', cm.exception['foo'])

    def test_convert_with_extra_value(self):
        self.values['extra'] = '123'

        with self.assertRaises(exceptions.ConfigError) as cm:
            self.schema.convert(self.values.items())

        self.assertIn('unknown', cm.exception['extra'])

    def test_convert_with_deserialization_error(self):
        self.schema['foo'].deserialize.side_effect = ValueError('failure')

        with self.assertRaises(exceptions.ConfigError) as cm:
            self.schema.convert(self.values.items())

        self.assertIn('failure', cm.exception['foo'])

    def test_convert_with_multiple_deserialization_errors(self):
        self.schema['foo'].deserialize.side_effect = ValueError('failure')
        self.schema['bar'].deserialize.side_effect = ValueError('other')

        with self.assertRaises(exceptions.ConfigError) as cm:
            self.schema.convert(self.values.items())

        self.assertIn('failure', cm.exception['foo'])
        self.assertIn('other', cm.exception['bar'])

    def test_convert_deserialization_unknown_and_missing_errors(self):
        self.values['extra'] = '123'
        self.schema['bar'].deserialize.side_effect = ValueError('failure')
        del self.values['baz']

        with self.assertRaises(exceptions.ConfigError) as cm:
            self.schema.convert(self.values.items())

        self.assertIn('unknown', cm.exception['extra'])
        self.assertNotIn('foo', cm.exception)
        self.assertIn('failure', cm.exception['bar'])
        self.assertIn('not found', cm.exception['baz'])


class ExtensionConfigSchemaTest(unittest.TestCase):
    def test_schema_includes_enabled(self):
        schema = config.ExtensionConfigSchema()
        self.assertIsInstance(schema['enabled'], config.Boolean)


class LogLevelConfigSchemaTest(unittest.TestCase):
    def test_conversion(self):
        schema = config.LogLevelConfigSchema()
        result = schema.convert([('foo.bar', 'DEBUG'), ('baz', 'INFO')])

        self.assertEqual(logging.DEBUG, result['foo.bar'])
        self.assertEqual(logging.INFO, result['baz'])

    def test_format(self):
        schema = config.LogLevelConfigSchema()
        expected = ['[levels]', 'baz = info', 'foo.bar = debug']
        result = schema.format('levels', {'foo.bar': logging.DEBUG, 'baz': logging.INFO})
        self.assertEqual('\n'.join(expected), result)

