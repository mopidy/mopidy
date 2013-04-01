from __future__ import unicode_literals

from mopidy.utils import config

from tests import unittest


class ValidateChoiceTest(unittest.TestCase):
    def test_no_choices_passes(self):
        config.validate_choice('foo', None)

    def test_valid_value_passes(self):
        config.validate_choice('foo', ['foo', 'bar', 'baz'])
        config.validate_choice(1, [1, 2, 3])

    def test_empty_choices_fails(self):
        with self.assertRaises(ValueError):
            config.validate_choice('foo', [])

    def test_invalid_value_fails(self):
        with self.assertRaises(ValueError):
            config.validate_choice('foobar', ['foo', 'bar', 'baz'])
        with self.assertRaises(ValueError):
            config.validate_choice(5, [1, 2, 3])


class ValidateMinimumTest(unittest.TestCase):
    def test_no_minimum_passes(self):
        config.validate_minimum(10, None)

    def test_valid_value_passes(self):
        config.validate_minimum(10, 5)

    def test_to_small_value_fails(self):
        with self.assertRaises(ValueError):
            config.validate_minimum(10, 20)

    def test_to_small_value_fails_with_zero_as_minimum(self):
        with self.assertRaises(ValueError):
            config.validate_minimum(-1, 0)


class ValidateMaximumTest(unittest.TestCase):
    def test_no_maximum_passes(self):
        config.validate_maximum(5, None)

    def test_valid_value_passes(self):
        config.validate_maximum(5, 10)

    def test_to_large_value_fails(self):
        with self.assertRaises(ValueError):
            config.validate_maximum(10, 5)

    def test_to_large_value_fails_with_zero_as_maximum(self):
        with self.assertRaises(ValueError):
            config.validate_maximum(5, 0)


class ConfigValueTest(unittest.TestCase):
    def test_init(self):
        value = config.ConfigValue()
        self.assertIsNone(value.choices)
        self.assertIsNone(value.minimum)
        self.assertIsNone(value.maximum)
        self.assertIsNone(value.secret)

    def test_init_with_params(self):
        value = config.ConfigValue(
            choices=['foo'], minimum=0, maximum=10, secret=True)
        self.assertEqual(['foo'], value.choices)
        self.assertEqual(0, value.minimum)
        self.assertEqual(10, value.maximum)
        self.assertEqual(True, value.secret)

    def test_deserialize_passes_through(self):
        value = config.ConfigValue()
        obj = object()
        self.assertEqual(obj, value.deserialize(obj))

    def test_serialize_converts_to_string(self):
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
    def test_deserialize_strips_whitespace(self):
        value = config.String()
        self.assertEqual('foo', value.deserialize(' foo '))

    def test_deserialize_enforces_choices(self):
        value = config.String(choices=['foo', 'bar', 'baz'])
        self.assertEqual('foo', value.deserialize('foo'))
        with self.assertRaises(ValueError):
            value.deserialize('foobar')

    def test_serialize_strips_whitespace(self):
        value = config.String()
        self.assertEqual('foo', value.serialize(' foo '))

    def test_format_masks_secrets(self):
        value = config.String(secret=True)
        self.assertEqual('********', value.format('s3cret'))


class IntegerTest(unittest.TestCase):
    def test_deserialize_converts_to_int(self):
        value = config.Integer()
        self.assertEqual(123, value.deserialize('123'))
        self.assertEqual(0, value.deserialize('0'))
        self.assertEqual(-10, value.deserialize('-10'))

    def test_deserialize_fails_on_bad_data(self):
        value = config.Integer()
        with self.assertRaises(ValueError):
            value.deserialize('asd')
        with self.assertRaises(ValueError):
            value.deserialize('3.14')

    def test_deserialize_enforces_choices(self):
        value = config.Integer(choices=[1, 2, 3])
        self.assertEqual(3, value.deserialize('3'))
        with self.assertRaises(ValueError):
            value.deserialize('5')

    def test_deserialize_enforces_minimum(self):
        value = config.Integer(minimum=10)
        self.assertEqual(15, value.deserialize('15'))
        with self.assertRaises(ValueError):
            value.deserialize('5')

    def test_deserialize_enforces_maximum(self):
        value = config.Integer(maximum=10)
        self.assertEqual(5, value.deserialize('5'))
        with self.assertRaises(ValueError):
            value.deserialize('15')

    def test_format_masks_secrets(self):
        value = config.Integer(secret=True)
        self.assertEqual('********', value.format('1337'))
