from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.config import validators


class ValidateChoiceTest(unittest.TestCase):

    def test_no_choices_passes(self):
        validators.validate_choice('foo', None)

    def test_valid_value_passes(self):
        validators.validate_choice('foo', ['foo', 'bar', 'baz'])
        validators.validate_choice(1, [1, 2, 3])

    def test_empty_choices_fails(self):
        self.assertRaises(ValueError, validators.validate_choice, 'foo', [])

    def test_invalid_value_fails(self):
        words = ['foo', 'bar', 'baz']
        self.assertRaises(
            ValueError, validators.validate_choice, 'foobar', words)
        self.assertRaises(
            ValueError, validators.validate_choice, 5, [1, 2, 3])


class ValidateMinimumTest(unittest.TestCase):

    def test_no_minimum_passes(self):
        validators.validate_minimum(10, None)

    def test_valid_value_passes(self):
        validators.validate_minimum(10, 5)

    def test_to_small_value_fails(self):
        self.assertRaises(ValueError, validators.validate_minimum, 10, 20)

    def test_to_small_value_fails_with_zero_as_minimum(self):
        self.assertRaises(ValueError, validators.validate_minimum, -1, 0)


class ValidateMaximumTest(unittest.TestCase):

    def test_no_maximum_passes(self):
        validators.validate_maximum(5, None)

    def test_valid_value_passes(self):
        validators.validate_maximum(5, 10)

    def test_to_large_value_fails(self):
        self.assertRaises(ValueError, validators.validate_maximum, 10, 5)

    def test_to_large_value_fails_with_zero_as_maximum(self):
        self.assertRaises(ValueError, validators.validate_maximum, 5, 0)


class ValidateRequiredTest(unittest.TestCase):

    def test_passes_when_false(self):
        validators.validate_required('foo', False)
        validators.validate_required('', False)
        validators.validate_required('  ', False)
        validators.validate_required([], False)

    def test_passes_when_required_and_set(self):
        validators.validate_required('foo', True)
        validators.validate_required(' foo ', True)
        validators.validate_required([1], True)

    def test_blocks_when_required_and_emtpy(self):
        self.assertRaises(ValueError, validators.validate_required, '', True)
        self.assertRaises(ValueError, validators.validate_required, [], True)
