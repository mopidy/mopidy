from __future__ import unicode_literals

import mock

from mopidy import config

from tests import unittest, path_to_data_dir


class LoadConfigTest(unittest.TestCase):
    def test_load_nothing(self):
        self.assertEqual({}, config._load([], [], []))

    def test_load_single_default(self):
        default = b'[foo]\nbar = baz'
        expected = {'foo': {'bar': 'baz'}}
        result = config._load([], [default], [])
        self.assertEqual(expected, result)

    def test_load_defaults(self):
        default1 = b'[foo]\nbar = baz'
        default2 = b'[foo2]\n'
        expected = {'foo': {'bar': 'baz'}, 'foo2': {}}
        result = config._load([], [default1, default2], [])
        self.assertEqual(expected, result)

    def test_load_single_override(self):
        override = ('foo', 'bar', 'baz')
        expected = {'foo': {'bar': 'baz'}}
        result = config._load([], [], [override])
        self.assertEqual(expected, result)

    def test_load_overrides(self):
        override1 = ('foo', 'bar', 'baz')
        override2 = ('foo2', 'bar', 'baz')
        expected = {'foo': {'bar': 'baz'}, 'foo2': {'bar': 'baz'}}
        result = config._load([], [], [override1, override2])
        self.assertEqual(expected, result)

    def test_load_single_file(self):
        file1 = path_to_data_dir('file1.conf')
        expected = {'foo': {'bar': 'baz'}}
        result = config._load([file1], [], [])
        self.assertEqual(expected, result)

    def test_load_files(self):
        file1 = path_to_data_dir('file1.conf')
        file2 = path_to_data_dir('file2.conf')
        expected = {'foo': {'bar': 'baz'}, 'foo2': {'bar': 'baz'}}
        result = config._load([file1, file2], [], [])
        self.assertEqual(expected, result)


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.schema = config.ConfigSchema('foo')
        self.schema['bar'] = config.ConfigValue()

    def test_empty_config_no_schemas(self):
        conf, errors = config._validate({}, [])
        self.assertEqual({}, conf)
        self.assertEqual({}, errors)

    def test_config_no_schemas(self):
        raw_config = {'foo': {'bar': 'baz'}}
        conf, errors = config._validate(raw_config, [])
        self.assertEqual({}, conf)
        self.assertEqual({}, errors)

    def test_empty_config_single_schema(self):
        conf, errors = config._validate({}, [self.schema])
        self.assertEqual({'foo': {'bar': None}}, conf)
        self.assertEqual({'foo': {'bar': 'config key not found.'}}, errors)

    def test_config_single_schema(self):
        raw_config = {'foo': {'bar': 'baz'}}
        conf, errors = config._validate(raw_config, [self.schema])
        self.assertEqual({'foo': {'bar': 'baz'}}, conf)
        self.assertEqual({}, errors)

    def test_config_single_schema_config_error(self):
        raw_config = {'foo': {'bar': 'baz'}}
        self.schema['bar'] = mock.Mock()
        self.schema['bar'].deserialize.side_effect = ValueError('bad')
        conf, errors = config._validate(raw_config, [self.schema])
        self.assertEqual({'foo': {'bar': None}}, conf)
        self.assertEqual({'foo': {'bar': 'bad'}}, errors)

    # TODO: add more tests


class ParseOverrideTest(unittest.TestCase):
    def test_valid_override(self):
        expected = ('section', 'key', 'value')
        self.assertEqual(expected, config.parse_override('section/key=value'))
        self.assertEqual(expected, config.parse_override('section/key=value '))
        self.assertEqual(expected, config.parse_override('section/key =value'))
        self.assertEqual(expected, config.parse_override('section /key=value'))

    def test_empty_override(self):
        expected = ('section', 'key', '')
        self.assertEqual(expected, config.parse_override('section/key='))
        self.assertEqual(expected, config.parse_override('section/key=  '))

    def test_invalid_override(self):
        self.assertRaises(ValueError, config.parse_override, 'section/key')
        self.assertRaises(ValueError, config.parse_override, 'section=')
        self.assertRaises(ValueError, config.parse_override, 'section')
