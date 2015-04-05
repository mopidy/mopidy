from __future__ import absolute_import, unicode_literals

import logging
import unittest

import mock

from mopidy.config import schemas, types

from tests import any_unicode


class ConfigSchemaTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.schema = schemas.ConfigSchema('test')
        self.schema['foo'] = mock.Mock()
        self.schema['bar'] = mock.Mock()
        self.schema['baz'] = mock.Mock()
        self.values = {'bar': '123', 'foo': '456', 'baz': '678'}

    def test_deserialize(self):
        self.schema.deserialize(self.values)

    def test_deserialize_with_missing_value(self):
        del self.values['foo']

        result, errors = self.schema.deserialize(self.values)
        self.assertEqual({'foo': any_unicode}, errors)
        self.assertIsNone(result.pop('foo'))
        self.assertIsNotNone(result.pop('bar'))
        self.assertIsNotNone(result.pop('baz'))
        self.assertEqual({}, result)

    def test_deserialize_with_extra_value(self):
        self.values['extra'] = '123'

        result, errors = self.schema.deserialize(self.values)
        self.assertEqual({'extra': any_unicode}, errors)
        self.assertIsNotNone(result.pop('foo'))
        self.assertIsNotNone(result.pop('bar'))
        self.assertIsNotNone(result.pop('baz'))
        self.assertEqual({}, result)

    def test_deserialize_with_deserialization_error(self):
        self.schema['foo'].deserialize.side_effect = ValueError('failure')

        result, errors = self.schema.deserialize(self.values)
        self.assertEqual({'foo': 'failure'}, errors)
        self.assertIsNone(result.pop('foo'))
        self.assertIsNotNone(result.pop('bar'))
        self.assertIsNotNone(result.pop('baz'))
        self.assertEqual({}, result)

    def test_deserialize_with_multiple_deserialization_errors(self):
        self.schema['foo'].deserialize.side_effect = ValueError('failure')
        self.schema['bar'].deserialize.side_effect = ValueError('other')

        result, errors = self.schema.deserialize(self.values)
        self.assertEqual({'foo': 'failure', 'bar': 'other'}, errors)
        self.assertIsNone(result.pop('foo'))
        self.assertIsNone(result.pop('bar'))
        self.assertIsNotNone(result.pop('baz'))
        self.assertEqual({}, result)

    def test_deserialize_deserialization_unknown_and_missing_errors(self):
        self.values['extra'] = '123'
        self.schema['bar'].deserialize.side_effect = ValueError('failure')
        del self.values['baz']

        result, errors = self.schema.deserialize(self.values)
        self.assertIn('unknown', errors['extra'])
        self.assertNotIn('foo', errors)
        self.assertIn('failure', errors['bar'])
        self.assertIn('not found', errors['baz'])

        self.assertNotIn('unknown', result)
        self.assertIn('foo', result)
        self.assertIsNone(result['bar'])
        self.assertIsNone(result['baz'])

    def test_deserialize_deprecated_value(self):
        self.schema['foo'] = types.Deprecated()

        result, errors = self.schema.deserialize(self.values)
        self.assertItemsEqual(['bar', 'baz'], result.keys())
        self.assertNotIn('foo', errors)


class MapConfigSchemaTest(unittest.TestCase):

    def test_conversion(self):
        schema = schemas.MapConfigSchema('test', types.LogLevel())
        result, errors = schema.deserialize(
            {'foo.bar': 'DEBUG', 'baz': 'INFO'})

        self.assertEqual(logging.DEBUG, result['foo.bar'])
        self.assertEqual(logging.INFO, result['baz'])


class DidYouMeanTest(unittest.TestCase):

    def test_suggestions(self):
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
