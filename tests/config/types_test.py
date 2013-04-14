# encoding: utf-8

from __future__ import unicode_literals

import logging
import mock
import socket

from mopidy.config import types

from tests import unittest

# TODO: DecodeTest and EncodeTest


class ConfigValueTest(unittest.TestCase):
    def test_init(self):
        value = types.ConfigValue()
        self.assertIsNone(value.choices)
        self.assertIsNone(value.maximum)
        self.assertIsNone(value.minimum)
        self.assertIsNone(value.optional)
        self.assertIsNone(value.secret)

    def test_init_with_params(self):
        kwargs = {'choices': ['foo'], 'minimum': 0, 'maximum': 10,
                  'secret': True, 'optional': True}
        value = types.ConfigValue(**kwargs)
        self.assertEqual(['foo'], value.choices)
        self.assertEqual(0, value.minimum)
        self.assertEqual(10, value.maximum)
        self.assertEqual(True, value.optional)
        self.assertEqual(True, value.secret)

    def test_deserialize_passes_through(self):
        value = types.ConfigValue()
        sentinel = object()
        self.assertEqual(sentinel, value.deserialize(sentinel))

    def test_serialize_conversion_to_string(self):
        value = types.ConfigValue()
        self.assertIsInstance(value.serialize(object()), bytes)

    def test_format_uses_serialize(self):
        value = types.ConfigValue()
        obj = object()
        self.assertEqual(value.serialize(obj), value.format(obj))

    def test_format_masks_secrets(self):
        value = types.ConfigValue(secret=True)
        self.assertEqual('********', value.format(object()))


class StringTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = types.String()
        self.assertEqual('foo', value.deserialize(b' foo '))
        self.assertIsInstance(value.deserialize(b'foo'), unicode)

    def test_deserialize_decodes_utf8(self):
        value = types.String()
        result = value.deserialize('æøå'.encode('utf-8'))
        self.assertEqual('æøå', result)

    def test_deserialize_does_not_double_encode_unicode(self):
        value = types.String()
        result = value.deserialize('æøå')
        self.assertEqual('æøå', result)

    def test_deserialize_handles_escapes(self):
        value = types.String(optional=True)
        result = value.deserialize(b'a\\t\\nb')
        self.assertEqual('a\t\nb', result)

    def test_deserialize_enforces_choices(self):
        value = types.String(choices=['foo', 'bar', 'baz'])
        self.assertEqual('foo', value.deserialize(b'foo'))
        self.assertRaises(ValueError, value.deserialize, b'foobar')

    def test_deserialize_enforces_required(self):
        value = types.String()
        self.assertRaises(ValueError, value.deserialize, b'')
        self.assertRaises(ValueError, value.deserialize, b' ')

    def test_deserialize_respects_optional(self):
        value = types.String(optional=True)
        self.assertIsNone(value.deserialize(b''))
        self.assertIsNone(value.deserialize(b' '))

    def test_deserialize_decode_failure(self):
        value = types.String()
        incorrectly_encoded_bytes = u'æøå'.encode('iso-8859-1')
        self.assertRaises(
            ValueError, value.deserialize, incorrectly_encoded_bytes)

    def test_serialize_encodes_utf8(self):
        value = types.String()
        result = value.serialize('æøå')
        self.assertIsInstance(result, bytes)
        self.assertEqual('æøå'.encode('utf-8'), result)

    def test_serialize_does_not_encode_bytes(self):
        value = types.String()
        result = value.serialize('æøå'.encode('utf-8'))
        self.assertIsInstance(result, bytes)
        self.assertEqual('æøå'.encode('utf-8'), result)

    def test_serialize_handles_escapes(self):
        value = types.String()
        result = value.serialize('a\n\tb')
        self.assertIsInstance(result, bytes)
        self.assertEqual(r'a\n\tb'.encode('utf-8'), result)

    def test_format_masks_secrets(self):
        value = types.String(secret=True)
        self.assertEqual('********', value.format('s3cret'))


class IntegerTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = types.Integer()
        self.assertEqual(123, value.deserialize('123'))
        self.assertEqual(0, value.deserialize('0'))
        self.assertEqual(-10, value.deserialize('-10'))

    def test_deserialize_conversion_failure(self):
        value = types.Integer()
        self.assertRaises(ValueError, value.deserialize, 'asd')
        self.assertRaises(ValueError, value.deserialize, '3.14')
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_deserialize_enforces_choices(self):
        value = types.Integer(choices=[1, 2, 3])
        self.assertEqual(3, value.deserialize('3'))
        self.assertRaises(ValueError, value.deserialize, '5')

    def test_deserialize_enforces_minimum(self):
        value = types.Integer(minimum=10)
        self.assertEqual(15, value.deserialize('15'))
        self.assertRaises(ValueError, value.deserialize, '5')

    def test_deserialize_enforces_maximum(self):
        value = types.Integer(maximum=10)
        self.assertEqual(5, value.deserialize('5'))
        self.assertRaises(ValueError, value.deserialize, '15')

    def test_format_masks_secrets(self):
        value = types.Integer(secret=True)
        self.assertEqual('********', value.format('1337'))


class BooleanTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = types.Boolean()
        for true in ('1', 'yes', 'true', 'on'):
            self.assertIs(value.deserialize(true), True)
            self.assertIs(value.deserialize(true.upper()), True)
            self.assertIs(value.deserialize(true.capitalize()), True)
        for false in ('0', 'no', 'false', 'off'):
            self.assertIs(value.deserialize(false), False)
            self.assertIs(value.deserialize(false.upper()), False)
            self.assertIs(value.deserialize(false.capitalize()), False)

    def test_deserialize_conversion_failure(self):
        value = types.Boolean()
        self.assertRaises(ValueError, value.deserialize, 'nope')
        self.assertRaises(ValueError, value.deserialize, 'sure')
        self.assertRaises(ValueError, value.deserialize, '')

    def test_serialize(self):
        value = types.Boolean()
        self.assertEqual('true', value.serialize(True))
        self.assertEqual('false', value.serialize(False))

    def test_format_masks_secrets(self):
        value = types.Boolean(secret=True)
        self.assertEqual('********', value.format('true'))


class ListTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        value = types.List()

        expected = ('foo', 'bar', 'baz')
        self.assertEqual(expected, value.deserialize('foo, bar ,baz '))

        expected = ('foo,bar', 'bar', 'baz')
        self.assertEqual(expected, value.deserialize(' foo,bar\nbar\nbaz'))

    def test_deserialize_enforces_required(self):
        value = types.List()
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_deserialize_respects_optional(self):
        value = types.List(optional=True)
        self.assertEqual(tuple(), value.deserialize(''))
        self.assertEqual(tuple(), value.deserialize(' '))

    def test_serialize(self):
        value = types.List()
        result = value.serialize(('foo', 'bar', 'baz'))
        self.assertRegexpMatches(result, r'foo\n\s*bar\n\s*baz')


class LogLevelTest(unittest.TestCase):
    levels = {'critical': logging.CRITICAL,
              'error': logging.ERROR,
              'warning': logging.WARNING,
              'info': logging.INFO,
              'debug': logging.DEBUG}

    def test_deserialize_conversion_success(self):
        value = types.LogLevel()
        for name, level in self.levels.items():
            self.assertEqual(level, value.deserialize(name))
            self.assertEqual(level, value.deserialize(name.upper()))
            self.assertEqual(level, value.deserialize(name.capitalize()))

    def test_deserialize_conversion_failure(self):
        value = types.LogLevel()
        self.assertRaises(ValueError, value.deserialize, 'nope')
        self.assertRaises(ValueError, value.deserialize, 'sure')
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_serialize(self):
        value = types.LogLevel()
        for name, level in self.levels.items():
            self.assertEqual(name, value.serialize(level))
        self.assertIsNone(value.serialize(1337))


class HostnameTest(unittest.TestCase):
    @mock.patch('socket.getaddrinfo')
    def test_deserialize_conversion_success(self, getaddrinfo_mock):
        value = types.Hostname()
        value.deserialize('example.com')
        getaddrinfo_mock.assert_called_once_with('example.com', None)

    @mock.patch('socket.getaddrinfo')
    def test_deserialize_conversion_failure(self, getaddrinfo_mock):
        value = types.Hostname()
        getaddrinfo_mock.side_effect = socket.error
        self.assertRaises(ValueError, value.deserialize, 'example.com')

    @mock.patch('socket.getaddrinfo')
    def test_deserialize_enforces_required(self, getaddrinfo_mock):
        value = types.Hostname()
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')
        self.assertEqual(0, getaddrinfo_mock.call_count)

    @mock.patch('socket.getaddrinfo')
    def test_deserialize_respects_optional(self, getaddrinfo_mock):
        value = types.Hostname(optional=True)
        self.assertIsNone(value.deserialize(''))
        self.assertIsNone(value.deserialize(' '))
        self.assertEqual(0, getaddrinfo_mock.call_count)


class PortTest(unittest.TestCase):
    def test_valid_ports(self):
        value = types.Port()
        self.assertEqual(1, value.deserialize('1'))
        self.assertEqual(80, value.deserialize('80'))
        self.assertEqual(6600, value.deserialize('6600'))
        self.assertEqual(65535, value.deserialize('65535'))

    def test_invalid_ports(self):
        value = types.Port()
        self.assertRaises(ValueError, value.deserialize, '65536')
        self.assertRaises(ValueError, value.deserialize, '100000')
        self.assertRaises(ValueError, value.deserialize, '0')
        self.assertRaises(ValueError, value.deserialize, '-1')
        self.assertRaises(ValueError, value.deserialize, '')


class ExpandedPathTest(unittest.TestCase):
    def test_is_bytes(self):
        self.assertIsInstance(types.ExpandedPath('/tmp'), bytes)

    @mock.patch('mopidy.utils.path.expand_path')
    def test_defaults_to_expanded(self, expand_path_mock):
        expand_path_mock.return_value = 'expanded_path'
        self.assertEqual('expanded_path', types.ExpandedPath('~'))

    @mock.patch('mopidy.utils.path.expand_path')
    def test_orginal_stores_unexpanded(self, expand_path_mock):
        self.assertEqual('~', types.ExpandedPath('~').original)


class PathTest(unittest.TestCase):
    def test_deserialize_conversion_success(self):
        result = types.Path().deserialize('/foo')
        self.assertEqual('/foo', result)
        self.assertIsInstance(result, types.ExpandedPath)
        self.assertIsInstance(result, bytes)

    def test_deserialize_enforces_choices(self):
        value = types.Path(choices=['/foo', '/bar', '/baz'])
        self.assertEqual('/foo', value.deserialize('/foo'))
        self.assertRaises(ValueError, value.deserialize, '/foobar')

    def test_deserialize_enforces_required(self):
        value = types.Path()
        self.assertRaises(ValueError, value.deserialize, '')
        self.assertRaises(ValueError, value.deserialize, ' ')

    def test_deserialize_respects_optional(self):
        value = types.Path(optional=True)
        self.assertIsNone(value.deserialize(''))
        self.assertIsNone(value.deserialize(' '))

    @mock.patch('mopidy.utils.path.expand_path')
    def test_serialize_uses_original(self, expand_path_mock):
        expand_path_mock.return_value = 'expanded_path'
        path = types.ExpandedPath('original_path')
        value = types.Path()
        self.assertEqual('expanded_path', path)
        self.assertEqual('original_path', value.serialize(path))

    def test_serialize_plain_string(self):
        value = types.Path()
        self.assertEqual('path', value.serialize('path'))
