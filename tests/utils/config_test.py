from __future__ import unicode_literals

from mopidy.utils import config

from tests import unittest


class ValidateChoiceTest(unittest.TestCase):
    def test_no_choices_passes(self):
        config.validate_choice('foo', None)

    def test_valid_value_passes(self):
        config.validate_choice('foo', ['foo', 'bar', 'baz'])

    def test_empty_choices_fails(self):
        with self.assertRaises(ValueError):
            config.validate_choice('foo', [])

    def test_invalid_value_fails(self):
        with self.assertRaises(ValueError):
            config.validate_choice('foobar', ['foo', 'bar', 'baz'])


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
