# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import logging
import socket
import unittest

import mock

from mopidy import compat
from mopidy.config import types

# TODO: DecodeTest and EncodeTest


class ConfigValueTest(unittest.TestCase):

    def test_deserialize_passes_through(self):
        value = types.ConfigValue()
        sentinel = object()
        self.assertEqual(sentinel, value.deserialize(sentinel))

    def test_serialize_conversion_to_string(self):
        value = types.ConfigValue()
        self.assertIsInstance(value.serialize(object()), bytes)

    def test_serialize_none(self):
        value = types.ConfigValue()
        result = value.serialize(None)
        self.assertIsInstance(result, bytes)
        self.assertEqual(b'', result)

    def test_serialize_supports_display(self):
        value = types.ConfigValue()
        self.assertIsInstance(value.serialize(object(), display=True), bytes)


class DeprecatedTest(unittest.TestCase):

    def test_deserialize_returns_deprecated_value(self):
        self.assertIsInstance(types.Deprecated().deserialize(b'foobar'),
                              types.DeprecatedValue)

    def test_serialize_returns_deprecated_value(self):
        self.assertIsInstance(types.Deprecated().serialize('foobar'),
                              types.DeprecatedValue)


class StringTest(unittest.TestCase):

    def test_deserialize_conversion_success(self):
        value = types.String()
        self.assertEqual('foo', value.deserialize(b' foo '))
        self.assertIsInstance(value.deserialize(b'foo'), compat.text_type)

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

    def test_serialize_none(self):
        value = types.String()
        result = value.serialize(None)
        self.assertIsInstance(result, bytes)
        self.assertEqual(b'', result)

    def test_deserialize_enforces_choices_optional(self):
        value = types.String(optional=True, choices=['foo', 'bar', 'baz'])
        self.assertEqual(None, value.deserialize(b''))
        self.assertRaises(ValueError, value.deserialize, b'foobar')


class SecretTest(unittest.TestCase):

    def test_deserialize_decodes_utf8(self):
        value = types.Secret()
        result = value.deserialize('æøå'.encode('utf-8'))
        self.assertIsInstance(result, compat.text_type)
        self.assertEqual('æøå', result)

    def test_deserialize_enforces_required(self):
        value = types.Secret()
        self.assertRaises(ValueError, value.deserialize, b'')

    def test_deserialize_respects_optional(self):
        value = types.Secret(optional=True)
        self.assertIsNone(value.deserialize(b''))
        self.assertIsNone(value.deserialize(b' '))

    def test_serialize_none(self):
        value = types.Secret()
        result = value.serialize(None)
        self.assertIsInstance(result, bytes)
        self.assertEqual(b'', result)

    def test_serialize_for_display_masks_value(self):
        value = types.Secret()
        result = value.serialize('s3cret', display=True)
        self.assertIsInstance(result, bytes)
        self.assertEqual(b'********', result)

    def test_serialize_none_for_display(self):
        value = types.Secret()
        result = value.serialize(None, display=True)
        self.assertIsInstance(result, bytes)
        self.assertEqual(b'', result)


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

    def test_deserialize_respects_optional(self):
        value = types.Integer(optional=True)
        self.assertEqual(None, value.deserialize(''))


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

    def test_serialize_true(self):
        value = types.Boolean()
        result = value.serialize(True)
        self.assertEqual(b'true', result)
        self.assertIsInstance(result, bytes)

    def test_serialize_false(self):
        value = types.Boolean()
        result = value.serialize(False)
        self.assertEqual(b'false', result)
        self.assertIsInstance(result, bytes)

    def test_deserialize_respects_optional(self):
        value = types.Boolean(optional=True)
        self.assertEqual(None, value.deserialize(''))

    # TODO: test None or other invalid values into serialize?


class ListTest(unittest.TestCase):
    # TODO: add test_deserialize_ignores_blank
    # TODO: add test_serialize_ignores_blank
    # TODO: add test_deserialize_handles_escapes

    def test_deserialize_conversion_success(self):
        value = types.List()

        expected = ('foo', 'bar', 'baz')
        self.assertEqual(expected, value.deserialize(b'foo, bar ,baz '))

        expected = ('foo,bar', 'bar', 'baz')
        self.assertEqual(expected, value.deserialize(b' foo,bar\nbar\nbaz'))

    def test_deserialize_creates_tuples(self):
        value = types.List(optional=True)
        self.assertIsInstance(value.deserialize(b'foo,bar,baz'), tuple)
        self.assertIsInstance(value.deserialize(b''), tuple)

    def test_deserialize_decodes_utf8(self):
        value = types.List()

        result = value.deserialize('æ, ø, å'.encode('utf-8'))
        self.assertEqual(('æ', 'ø', 'å'), result)

        result = value.deserialize('æ\nø\nå'.encode('utf-8'))
        self.assertEqual(('æ', 'ø', 'å'), result)

    def test_deserialize_does_not_double_encode_unicode(self):
        value = types.List()

        result = value.deserialize('æ, ø, å')
        self.assertEqual(('æ', 'ø', 'å'), result)

        result = value.deserialize('æ\nø\nå')
        self.assertEqual(('æ', 'ø', 'å'), result)

    def test_deserialize_enforces_required(self):
        value = types.List()
        self.assertRaises(ValueError, value.deserialize, b'')

    def test_deserialize_respects_optional(self):
        value = types.List(optional=True)
        self.assertEqual(tuple(), value.deserialize(b''))

    def test_serialize(self):
        value = types.List()
        result = value.serialize(('foo', 'bar', 'baz'))
        self.assertIsInstance(result, bytes)
        self.assertRegexpMatches(result, r'foo\n\s*bar\n\s*baz')

    def test_serialize_none(self):
        value = types.List()
        result = value.serialize(None)
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, '')


class LogLevelTest(unittest.TestCase):
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
        'all': logging.NOTSET,
    }

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
        self.assertEqual(b'', value.serialize(1337))


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
        self.assertEqual(0, value.deserialize('0'))
        self.assertEqual(1, value.deserialize('1'))
        self.assertEqual(80, value.deserialize('80'))
        self.assertEqual(6600, value.deserialize('6600'))
        self.assertEqual(65535, value.deserialize('65535'))

    def test_invalid_ports(self):
        value = types.Port()
        self.assertRaises(ValueError, value.deserialize, '65536')
        self.assertRaises(ValueError, value.deserialize, '100000')
        self.assertRaises(ValueError, value.deserialize, '-1')
        self.assertRaises(ValueError, value.deserialize, '')


class ExpandedPathTest(unittest.TestCase):

    def test_is_bytes(self):
        self.assertIsInstance(types.ExpandedPath(b'/tmp', b'foo'), bytes)

    def test_defaults_to_expanded(self):
        original = b'~'
        expanded = b'expanded_path'
        self.assertEqual(expanded, types.ExpandedPath(original, expanded))

    @mock.patch('mopidy.internal.path.expand_path')
    def test_orginal_stores_unexpanded(self, expand_path_mock):
        original = b'~'
        expanded = b'expanded_path'
        result = types.ExpandedPath(original, expanded)
        self.assertEqual(original, result.original)


class PathTest(unittest.TestCase):

    def test_deserialize_conversion_success(self):
        result = types.Path().deserialize(b'/foo')
        self.assertEqual('/foo', result)
        self.assertIsInstance(result, types.ExpandedPath)
        self.assertIsInstance(result, bytes)

    def test_deserialize_enforces_required(self):
        value = types.Path()
        self.assertRaises(ValueError, value.deserialize, b'')

    def test_deserialize_respects_optional(self):
        value = types.Path(optional=True)
        self.assertIsNone(value.deserialize(b''))
        self.assertIsNone(value.deserialize(b' '))

    def test_serialize_uses_original(self):
        path = types.ExpandedPath(b'original_path', b'expanded_path')
        value = types.Path()
        self.assertEqual('expanded_path', path)
        self.assertEqual('original_path', value.serialize(path))

    def test_serialize_plain_string(self):
        value = types.Path()
        self.assertEqual('path', value.serialize(b'path'))

    def test_serialize_unicode_string(self):
        value = types.Path()
        self.assertRaises(ValueError, value.serialize, 'æøå')
