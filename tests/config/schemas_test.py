from __future__ import unicode_literals

import logging
import mock

from mopidy import exceptions
from mopidy.config import schemas, types

from tests import unittest


class ConfigSchemaTest(unittest.TestCase):
    def setUp(self):
        self.schema = schemas.ConfigSchema('test')
        self.schema['foo'] = mock.Mock()
        self.schema['bar'] = mock.Mock()
        self.schema['baz'] = mock.Mock()
        self.values = {'bar': '123', 'foo': '456', 'baz': '678'}

    def test_format(self):
        self.schema['foo'].format.return_value = 'qwe'
        self.schema['bar'].format.return_value = 'asd'
        self.schema['baz'].format.return_value = 'zxc'

        expected = ['[test]', 'foo = qwe', 'bar = asd', 'baz = zxc']
        result = self.schema.format(self.values)
        self.assertEqual('\n'.join(expected), result)

    def test_format_unkwown_value(self):
        self.schema['foo'].format.return_value = 'qwe'
        self.schema['bar'].format.return_value = 'asd'
        self.schema['baz'].format.return_value = 'zxc'
        self.values['unknown'] = 'rty'

        result = self.schema.format(self.values)
        self.assertNotIn('unknown = rty', result)

    def test_convert(self):
        self.schema.convert(self.values)

    def test_convert_with_missing_value(self):
        del self.values['foo']

        result, errors = self.schema.convert(self.values)
        self.assertIn('not found', errors['foo'])
        self.assertItemsEqual(['bar', 'baz'], result.keys())

    def test_convert_with_extra_value(self):
        self.values['extra'] = '123'

        result, errors = self.schema.convert(self.values)
        self.assertIn('unknown', errors['extra'])
        self.assertItemsEqual(['foo', 'bar', 'baz'], result.keys())

    def test_convert_with_deserialization_error(self):
        self.schema['foo'].deserialize.side_effect = ValueError('failure')

        result, errors = self.schema.convert(self.values)
        self.assertIn('failure', errors['foo'])
        self.assertItemsEqual(['bar', 'baz'], result.keys())

    def test_convert_with_multiple_deserialization_errors(self):
        self.schema['foo'].deserialize.side_effect = ValueError('failure')
        self.schema['bar'].deserialize.side_effect = ValueError('other')

        result, errors = self.schema.convert(self.values)
        self.assertIn('failure', errors['foo'])
        self.assertIn('other', errors['bar'])
        self.assertItemsEqual(['baz'], result.keys())

    def test_convert_deserialization_unknown_and_missing_errors(self):
        self.values['extra'] = '123'
        self.schema['bar'].deserialize.side_effect = ValueError('failure')
        del self.values['baz']

        result, errors = self.schema.convert(self.values)
        self.assertIn('unknown', errors['extra'])
        self.assertNotIn('foo', errors)
        self.assertIn('failure', errors['bar'])
        self.assertIn('not found', errors['baz'])
        self.assertItemsEqual(['foo'], result.keys())


class ExtensionConfigSchemaTest(unittest.TestCase):
    def test_schema_includes_enabled(self):
        schema = schemas.ExtensionConfigSchema('test')
        self.assertIsInstance(schema['enabled'], types.Boolean)


class LogLevelConfigSchemaTest(unittest.TestCase):
    def test_conversion(self):
        schema = schemas.LogLevelConfigSchema('test')
        result, errors = schema.convert({'foo.bar': 'DEBUG', 'baz': 'INFO'})

        self.assertEqual(logging.DEBUG, result['foo.bar'])
        self.assertEqual(logging.INFO, result['baz'])

    def test_format(self):
        schema = schemas.LogLevelConfigSchema('test')
        values = {'foo.bar': logging.DEBUG, 'baz': logging.INFO}
        expected = ['[test]', 'baz = info', 'foo.bar = debug']
        result = schema.format(values)
        self.assertEqual('\n'.join(expected), result)


class DidYouMeanTest(unittest.TestCase):
    def testSuggestoins(self):
        choices = ('enabled', 'username', 'password', 'bitrate', 'timeout')

        suggestion = schemas._did_you_mean('bitrate', choices)
        self.assertEqual(suggestion, 'bitrate')

        suggestion = schemas._did_you_mean('bitrote', choices)
        self.assertEqual(suggestion, 'bitrate')

        suggestion = schemas._did_you_mean('Bitrot', choices)
        self.assertEqual(suggestion, 'bitrate')

        suggestion = schemas._did_you_mean('BTROT', choices)
        self.assertEqual(suggestion, 'bitrate')

        suggestion = schemas._did_you_mean('btro', choices)
        self.assertEqual(suggestion, None)
