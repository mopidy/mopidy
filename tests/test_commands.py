from __future__ import absolute_import, unicode_literals

import argparse
import unittest

import mock

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
        with self.assertRaises(argparse.ArgumentTypeError):
            commands.config_override_type(b'section/key')
        with self.assertRaises(argparse.ArgumentTypeError):
            commands.config_override_type(b'section=')
        with self.assertRaises(argparse.ArgumentTypeError):
            commands.config_override_type(b'section')


class CommandParsingTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.exit_patcher = mock.patch.object(commands.Command, 'exit')
        self.exit_mock = self.exit_patcher.start()
        self.exit_mock.side_effect = SystemExit

    def tearDown(self):  # noqa: N802
        self.exit_patcher.stop()

    def test_command_parsing_returns_namespace(self):
        cmd = commands.Command()
        self.assertIsInstance(cmd.parse([]), argparse.Namespace)

    def test_command_parsing_does_not_contain_args(self):
        cmd = commands.Command()
        result = cmd.parse([])
        self.assertFalse(hasattr(result, '_args'))

    def test_unknown_options_bails(self):
        cmd = commands.Command()
        with self.assertRaises(SystemExit):
            cmd.parse(['--foobar'])

    def test_invalid_sub_command_bails(self):
        cmd = commands.Command()
        with self.assertRaises(SystemExit):
            cmd.parse(['foo'])

    def test_command_arguments(self):
        cmd = commands.Command()
        cmd.add_argument('--bar')

        result = cmd.parse(['--bar', 'baz'])
        self.assertEqual(result.bar, 'baz')

    def test_command_arguments_and_sub_command(self):
        child = commands.Command()
        child.add_argument('--baz')

        cmd = commands.Command()
        cmd.add_argument('--bar')
        cmd.add_child('foo', child)

        result = cmd.parse(['--bar', 'baz', 'foo'])
        self.assertEqual(result.bar, 'baz')
        self.assertEqual(result.baz, None)

    def test_subcommand_may_have_positional(self):
        child = commands.Command()
        child.add_argument('bar')

        cmd = commands.Command()
        cmd.add_child('foo', child)

        result = cmd.parse(['foo', 'baz'])
        self.assertEqual(result.bar, 'baz')

    def test_subcommand_may_have_remainder(self):
        child = commands.Command()
        child.add_argument('bar', nargs=argparse.REMAINDER)

        cmd = commands.Command()
        cmd.add_child('foo', child)

        result = cmd.parse(['foo', 'baz', 'bep', 'bop'])
        self.assertEqual(result.bar, ['baz', 'bep', 'bop'])

    def test_result_stores_choosen_command(self):
        child = commands.Command()

        cmd = commands.Command()
        cmd.add_child('foo', child)

        result = cmd.parse(['foo'])
        self.assertEqual(result.command, child)

        result = cmd.parse([])
        self.assertEqual(result.command, cmd)

        child2 = commands.Command()
        cmd.add_child('bar', child2)

        subchild = commands.Command()
        child.add_child('baz', subchild)

        result = cmd.parse(['bar'])
        self.assertEqual(result.command, child2)

        result = cmd.parse(['foo', 'baz'])
        self.assertEqual(result.command, subchild)

    def test_invalid_type(self):
        cmd = commands.Command()
        cmd.add_argument('--bar', type=int)

        with self.assertRaises(SystemExit):
            cmd.parse(['--bar', b'zero'], prog='foo')

        self.exit_mock.assert_called_once_with(
            1, "argument --bar: invalid int value: 'zero'",
            'usage: foo [--bar BAR]')

    @mock.patch('sys.argv')
    def test_command_error_usage_prog(self, argv_mock):
        argv_mock.__getitem__.return_value = '/usr/bin/foo'

        cmd = commands.Command()
        cmd.add_argument('--bar', required=True)

        with self.assertRaises(SystemExit):
            cmd.parse([])
        self.exit_mock.assert_called_once_with(
            mock.ANY, mock.ANY, 'usage: foo --bar BAR')

        self.exit_mock.reset_mock()
        with self.assertRaises(SystemExit):
            cmd.parse([], prog='baz')

        self.exit_mock.assert_called_once_with(
            mock.ANY, mock.ANY, 'usage: baz --bar BAR')

    def test_missing_required(self):
        cmd = commands.Command()
        cmd.add_argument('--bar', required=True)

        with self.assertRaises(SystemExit):
            cmd.parse([], prog='foo')

        self.exit_mock.assert_called_once_with(
            1, 'argument --bar is required', 'usage: foo --bar BAR')

    def test_missing_positionals(self):
        cmd = commands.Command()
        cmd.add_argument('bar')

        with self.assertRaises(SystemExit):
            cmd.parse([], prog='foo')

        self.exit_mock.assert_called_once_with(
            1, 'too few arguments', 'usage: foo bar')

    def test_missing_positionals_subcommand(self):
        child = commands.Command()
        child.add_argument('baz')

        cmd = commands.Command()
        cmd.add_child('bar', child)

        with self.assertRaises(SystemExit):
            cmd.parse(['bar'], prog='foo')

        self.exit_mock.assert_called_once_with(
            1, 'too few arguments', 'usage: foo bar baz')

    def test_unknown_command(self):
        cmd = commands.Command()

        with self.assertRaises(SystemExit):
            cmd.parse(['--help'], prog='foo')

        self.exit_mock.assert_called_once_with(
            1, 'unrecognized arguments: --help', 'usage: foo')

    def test_invalid_subcommand(self):
        cmd = commands.Command()
        cmd.add_child('baz', commands.Command())

        with self.assertRaises(SystemExit):
            cmd.parse(['bar'], prog='foo')

        self.exit_mock.assert_called_once_with(
            1, 'unrecognized command: bar', 'usage: foo')

    def test_set(self):
        cmd = commands.Command()
        cmd.set(foo='bar')

        result = cmd.parse([])
        self.assertEqual(result.foo, 'bar')

    def test_set_propegate(self):
        child = commands.Command()

        cmd = commands.Command()
        cmd.set(foo='bar')
        cmd.add_child('command', child)

        result = cmd.parse(['command'])
        self.assertEqual(result.foo, 'bar')

    def test_innermost_set_wins(self):
        child = commands.Command()
        child.set(foo='bar', baz=1)

        cmd = commands.Command()
        cmd.set(foo='baz', baz=None)
        cmd.add_child('command', child)

        result = cmd.parse(['command'])
        self.assertEqual(result.foo, 'bar')
        self.assertEqual(result.baz, 1)

    def test_help_action_works(self):
        cmd = commands.Command()
        cmd.add_argument('-h', action='help')
        cmd.format_help = mock.Mock()

        with self.assertRaises(SystemExit):
            cmd.parse(['-h'])

        cmd.format_help.assert_called_once_with(mock.ANY)
        self.exit_mock.assert_called_once_with(0, cmd.format_help.return_value)


class UsageTest(unittest.TestCase):

    @mock.patch('sys.argv')
    def test_prog_name_default_and_override(self, argv_mock):
        argv_mock.__getitem__.return_value = '/usr/bin/foo'
        cmd = commands.Command()
        self.assertEqual('usage: foo', cmd.format_usage().strip())
        self.assertEqual('usage: baz', cmd.format_usage('baz').strip())

    def test_basic_usage(self):
        cmd = commands.Command()
        self.assertEqual('usage: foo', cmd.format_usage('foo').strip())

        cmd.add_argument('-h', '--help', action='store_true')
        self.assertEqual('usage: foo [-h]', cmd.format_usage('foo').strip())

        cmd.add_argument('bar')
        self.assertEqual('usage: foo [-h] bar',
                         cmd.format_usage('foo').strip())

    def test_nested_usage(self):
        child = commands.Command()
        cmd = commands.Command()
        cmd.add_child('bar', child)

        self.assertEqual('usage: foo', cmd.format_usage('foo').strip())
        self.assertEqual('usage: foo bar', cmd.format_usage('foo bar').strip())

        cmd.add_argument('-h', '--help', action='store_true')
        self.assertEqual('usage: foo bar',
                         child.format_usage('foo bar').strip())

        child.add_argument('-h', '--help', action='store_true')
        self.assertEqual('usage: foo bar [-h]',
                         child.format_usage('foo bar').strip())


class HelpTest(unittest.TestCase):

    @mock.patch('sys.argv')
    def test_prog_name_default_and_override(self, argv_mock):
        argv_mock.__getitem__.return_value = '/usr/bin/foo'
        cmd = commands.Command()
        self.assertEqual('usage: foo', cmd.format_help().strip())
        self.assertEqual('usage: bar', cmd.format_help('bar').strip())

    def test_command_without_documenation_or_options(self):
        cmd = commands.Command()
        self.assertEqual('usage: bar', cmd.format_help('bar').strip())

    def test_command_with_option(self):
        cmd = commands.Command()
        cmd.add_argument('-h', '--help', action='store_true',
                         help='show this message')

        expected = ('usage: foo [-h]\n\n'
                    'OPTIONS:\n\n'
                    '  -h, --help  show this message')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_command_with_option_and_positional(self):
        cmd = commands.Command()
        cmd.add_argument('-h', '--help', action='store_true',
                         help='show this message')
        cmd.add_argument('bar', help='some help text')

        expected = ('usage: foo [-h] bar\n\n'
                    'OPTIONS:\n\n'
                    '  -h, --help  show this message\n'
                    '  bar         some help text')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_command_with_documentation(self):
        cmd = commands.Command()
        cmd.help = 'some text about everything this command does.'

        expected = ('usage: foo\n\n'
                    'some text about everything this command does.')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_command_with_documentation_and_option(self):
        cmd = commands.Command()
        cmd.help = 'some text about everything this command does.'
        cmd.add_argument('-h', '--help', action='store_true',
                         help='show this message')

        expected = ('usage: foo [-h]\n\n'
                    'some text about everything this command does.\n\n'
                    'OPTIONS:\n\n'
                    '  -h, --help  show this message')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_subcommand_without_documentation_or_options(self):
        child = commands.Command()
        cmd = commands.Command()
        cmd.add_child('bar', child)

        self.assertEqual('usage: foo', cmd.format_help('foo').strip())

    def test_subcommand_with_documentation_shown(self):
        child = commands.Command()
        child.help = 'some text about everything this command does.'

        cmd = commands.Command()
        cmd.add_child('bar', child)
        expected = ('usage: foo\n\n'
                    'COMMANDS:\n\n'
                    'bar\n\n'
                    '  some text about everything this command does.')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_subcommand_with_options_shown(self):
        child = commands.Command()
        child.add_argument('-h', '--help', action='store_true',
                           help='show this message')

        cmd = commands.Command()
        cmd.add_child('bar', child)

        expected = ('usage: foo\n\n'
                    'COMMANDS:\n\n'
                    'bar [-h]\n\n'
                    '    -h, --help  show this message')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_subcommand_with_positional_shown(self):
        child = commands.Command()
        child.add_argument('baz', help='the great and wonderful')

        cmd = commands.Command()
        cmd.add_child('bar', child)

        expected = ('usage: foo\n\n'
                    'COMMANDS:\n\n'
                    'bar baz\n\n'
                    '    baz  the great and wonderful')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_subcommand_with_options_and_documentation(self):
        child = commands.Command()
        child.help = '  some text about everything this command does.'
        child.add_argument('-h', '--help', action='store_true',
                           help='show this message')

        cmd = commands.Command()
        cmd.add_child('bar', child)

        expected = ('usage: foo\n\n'
                    'COMMANDS:\n\n'
                    'bar [-h]\n\n'
                    '  some text about everything this command does.\n\n'
                    '    -h, --help  show this message')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_nested_subcommands_with_options(self):
        subchild = commands.Command()
        subchild.add_argument('--test', help='the great and wonderful')

        child = commands.Command()
        child.add_child('baz', subchild)
        child.add_argument('-h', '--help', action='store_true',
                           help='show this message')

        cmd = commands.Command()
        cmd.add_child('bar', child)

        expected = ('usage: foo\n\n'
                    'COMMANDS:\n\n'
                    'bar [-h]\n\n'
                    '    -h, --help  show this message\n\n'
                    'bar baz [--test TEST]\n\n'
                    '    --test TEST  the great and wonderful')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_nested_subcommands_skipped_intermediate(self):
        subchild = commands.Command()
        subchild.add_argument('--test', help='the great and wonderful')

        child = commands.Command()
        child.add_child('baz', subchild)

        cmd = commands.Command()
        cmd.add_child('bar', child)

        expected = ('usage: foo\n\n'
                    'COMMANDS:\n\n'
                    'bar baz [--test TEST]\n\n'
                    '    --test TEST  the great and wonderful')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_command_with_option_and_subcommand_with_option(self):
        child = commands.Command()
        child.add_argument('--test', help='the great and wonderful')

        cmd = commands.Command()
        cmd.add_argument('-h', '--help', action='store_true',
                         help='show this message')
        cmd.add_child('bar', child)

        expected = ('usage: foo [-h]\n\n'
                    'OPTIONS:\n\n'
                    '  -h, --help  show this message\n\n'
                    'COMMANDS:\n\n'
                    'bar [--test TEST]\n\n'
                    '    --test TEST  the great and wonderful')
        self.assertEqual(expected, cmd.format_help('foo').strip())

    def test_command_with_options_doc_and_subcommand_with_option_and_doc(self):
        child = commands.Command()
        child.help = 'some text about this sub-command.'
        child.add_argument('--test', help='the great and wonderful')

        cmd = commands.Command()
        cmd.help = 'some text about everything this command does.'
        cmd.add_argument('-h', '--help', action='store_true',
                         help='show this message')
        cmd.add_child('bar', child)

        expected = ('usage: foo [-h]\n\n'
                    'some text about everything this command does.\n\n'
                    'OPTIONS:\n\n'
                    '  -h, --help  show this message\n\n'
                    'COMMANDS:\n\n'
                    'bar [--test TEST]\n\n'
                    '  some text about this sub-command.\n\n'
                    '    --test TEST  the great and wonderful')
        self.assertEqual(expected, cmd.format_help('foo').strip())


class RunTest(unittest.TestCase):

    def test_default_implmentation_raises_error(self):
        with self.assertRaises(NotImplementedError):
            commands.Command().run()
