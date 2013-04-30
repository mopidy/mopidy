from __future__ import unicode_literals

import argparse
import unittest

from mopidy import commands


class ConfigOverrideTypeTest(unittest.TestCase):
    def test_valid_override(self):
        expected = (b'section', b'key', b'value')
        self.assertEqual(
            expected, commands.config_override_type(b'section/key=value'))
        self.assertEqual(
            expected, commands.config_override_type(b'section/key=value '))
        self.assertEqual(
            expected, commands.config_override_type(b'section/key =value'))
        self.assertEqual(
            expected, commands.config_override_type(b'section /key=value'))

    def test_valid_override_is_bytes(self):
        section, key, value = commands.config_override_type(
            b'section/key=value')
        self.assertIsInstance(section, bytes)
        self.assertIsInstance(key, bytes)
        self.assertIsInstance(value, bytes)

    def test_empty_override(self):
        expected = ('section', 'key', '')
        self.assertEqual(
            expected, commands.config_override_type(b'section/key='))
        self.assertEqual(
            expected, commands.config_override_type(b'section/key=  '))

    def test_invalid_override(self):
        self.assertRaises(
            argparse.ArgumentTypeError,
            commands.config_override_type, b'section/key')
        self.assertRaises(
            argparse.ArgumentTypeError,
            commands.config_override_type, b'section=')
        self.assertRaises(
            argparse.ArgumentTypeError,
            commands.config_override_type, b'section')
