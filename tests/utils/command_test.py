from __future__ import unicode_literals

import argparse
import mock
import unittest

from mopidy.utils import command


class CommandParsingTest(unittest.TestCase):
    def test_command_parsing_returns_namespace(self):
        cmd = command.Command()
        self.assertIsInstance(cmd.parse([]), argparse.Namespace)

    def test_command_parsing_does_not_contain_args(self):
        cmd = command.Command()
        result = cmd.parse([])
        self.assertFalse(hasattr(result, '_args'))

    def test_sub_command_delegation(self):
        mock_cmd = mock.Mock(spec=command.Command)

        cmd = command.Command()
        cmd.add_child('foo', mock_cmd)

        cmd.parse(['foo'])
        mock_cmd.parse.assert_called_with([], mock.ANY)

    def test_unknown_options_raises_error(self):
        cmd = command.Command()
        with self.assertRaises(command.CommandError):
            cmd.parse(['--foobar'])

    def test_invalid_sub_command_raises_error(self):
        cmd = command.Command()
        with self.assertRaises(command.CommandError):
            cmd.parse(['foo'])

    def test_command_arguments(self):
        cmd = command.Command()
        cmd.add_argument('--bar')

        result = cmd.parse(['--bar', 'baz'])
        self.assertEqual(result.bar, 'baz')

    def test_command_arguments_and_sub_command(self):
        child = command.Command()
        child.add_argument('--baz')

        cmd = command.Command()
        cmd.add_argument('--bar')
        cmd.add_child('foo', child)

        result = cmd.parse(['--bar', 'baz', 'foo'])
        self.assertEqual(result.bar, 'baz')
        self.assertEqual(result.baz, None)

    def test_multiple_sub_commands(self):
        mock_foo_cmd = mock.Mock(spec=command.Command)
        mock_bar_cmd = mock.Mock(spec=command.Command)
        mock_baz_cmd = mock.Mock(spec=command.Command)

        cmd = command.Command()
        cmd.add_child('foo', mock_foo_cmd)
        cmd.add_child('bar', mock_bar_cmd)
        cmd.add_child('baz', mock_baz_cmd)

        cmd.parse(['bar'])
        mock_bar_cmd.parse.assert_called_with([], mock.ANY)

        cmd.parse(['baz'])
        mock_baz_cmd.parse.assert_called_with([], mock.ANY)

    def test_subcommand_may_have_positional(self):
        child = command.Command()
        child.add_argument('bar')

        cmd = command.Command()
        cmd.add_child('foo', child)

        result = cmd.parse(['foo', 'baz'])
        self.assertEqual(result.bar, 'baz')

    def test_subcommand_may_have_remainder(self):
        child = command.Command()
        child.add_argument('bar', nargs=argparse.REMAINDER)

        cmd = command.Command()
        cmd.add_child('foo', child)

        result = cmd.parse(['foo', 'baz', 'bep', 'bop'])
        self.assertEqual(result.bar, ['baz', 'bep', 'bop'])

    def test_result_stores_choosen_command(self):
        child = command.Command()

        cmd = command.Command()
        cmd.add_child('foo', child)

        result = cmd.parse(['foo'])
        self.assertEqual(result.command, child)

        result = cmd.parse([])
        self.assertEqual(result.command, cmd)

    def test_missing_positionals(self):
        cmd = command.Command()
        cmd.add_argument('foo')

        with self.assertRaises(command.CommandError):
            cmd.parse([])


class UsageTest(unittest.TestCase):
    @mock.patch('sys.argv')
    def test_basic_usage(self, argv_mock):
        argv_mock.__getitem__.return_value = 'foo'

        cmd = command.Command()
        self.assertEqual('usage: foo', cmd.format_usage().strip())

        self.assertEqual('usage: baz', cmd.format_usage('baz').strip())

        cmd.add_argument('-h', '--help', action='store_true')
        self.assertEqual('usage: foo [-h]', cmd.format_usage().strip())

        cmd.add_argument('bar')
        self.assertEqual('usage: foo [-h] bar', cmd.format_usage().strip())

    @mock.patch('sys.argv')
    def test_nested_usage(self, argv_mock):
        argv_mock.__getitem__.return_value = 'foo'

        child = command.Command()
        cmd = command.Command()
        cmd.add_child('bar', child)

        self.assertEqual('usage: foo', cmd.format_usage().strip())
        self.assertEqual('usage: foo bar', cmd.format_usage('foo bar').strip())

        cmd.add_argument('-h', '--help', action='store_true')
        self.assertEqual('usage: foo bar',
                         child.format_usage('foo bar').strip())

        child.add_argument('-h', '--help', action='store_true')
        self.assertEqual('usage: foo bar [-h]',
                         child.format_usage('foo bar').strip())
