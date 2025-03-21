import argparse
import re
import unittest
from unittest import mock

import pytest

from mopidy import commands


class ConfigOverrideTypeTest(unittest.TestCase):
    def test_valid_override(self):
        expected = ("section", "key", "value")
        assert expected == commands.config_override_type("section/key=value")
        assert expected == commands.config_override_type("section/key=value ")
        assert expected == commands.config_override_type("section/key =value")
        assert expected == commands.config_override_type("section /key=value")

    def test_empty_override(self):
        expected = ("section", "key", "")
        assert expected == commands.config_override_type("section/key=")
        assert expected == commands.config_override_type("section/key=  ")

    def test_invalid_override(self):
        with pytest.raises(argparse.ArgumentTypeError):
            commands.config_override_type("section/key")
        with pytest.raises(argparse.ArgumentTypeError):
            commands.config_override_type("section=")
        with pytest.raises(argparse.ArgumentTypeError):
            commands.config_override_type("section")


class CommandParsingTest(unittest.TestCase):
    def setUp(self):
        self.exit_patcher = mock.patch.object(commands.Command, "exit")
        self.exit_mock = self.exit_patcher.start()
        self.exit_mock.side_effect = SystemExit

    def tearDown(self):
        self.exit_patcher.stop()

    def test_command_parsing_returns_namespace(self):
        cmd = commands.Command()
        assert isinstance(cmd.parse([]), argparse.Namespace)

    def test_command_parsing_does_not_contain_args(self):
        cmd = commands.Command()
        result = cmd.parse([])
        assert not hasattr(result, "_args")

    def test_unknown_options_bails(self):
        cmd = commands.Command()
        with pytest.raises(SystemExit):
            cmd.parse(["--foobar"])

    def test_invalid_sub_command_bails(self):
        cmd = commands.Command()
        with pytest.raises(SystemExit):
            cmd.parse(["foo"])

    def test_command_arguments(self):
        cmd = commands.Command()
        cmd.add_argument("--bar")

        result = cmd.parse(["--bar", "baz"])
        assert result.bar == "baz"

    def test_command_arguments_and_sub_command(self):
        child = commands.Command()
        child.add_argument("--baz")

        cmd = commands.Command()
        cmd.add_argument("--bar")
        cmd.add_child("foo", child)

        result = cmd.parse(["--bar", "baz", "foo"])
        assert result.bar == "baz"
        assert result.baz is None

    def test_subcommand_may_have_positional(self):
        child = commands.Command()
        child.add_argument("bar")

        cmd = commands.Command()
        cmd.add_child("foo", child)

        result = cmd.parse(["foo", "baz"])
        assert result.bar == "baz"

    def test_subcommand_may_have_remainder(self):
        child = commands.Command()
        child.add_argument("bar", nargs=argparse.REMAINDER)

        cmd = commands.Command()
        cmd.add_child("foo", child)

        result = cmd.parse(["foo", "baz", "bep", "bop"])
        assert result.bar == ["baz", "bep", "bop"]

    def test_result_stores_chosen_command(self):
        child = commands.Command()

        cmd = commands.Command()
        cmd.add_child("foo", child)

        result = cmd.parse(["foo"])
        assert result.command == child

        result = cmd.parse([])
        assert result.command == cmd

        child2 = commands.Command()
        cmd.add_child("bar", child2)

        subchild = commands.Command()
        child.add_child("baz", subchild)

        result = cmd.parse(["bar"])
        assert result.command == child2

        result = cmd.parse(["foo", "baz"])
        assert result.command == subchild

    def test_invalid_type(self):
        cmd = commands.Command()
        cmd.add_argument("--bar", type=int)

        with pytest.raises(SystemExit):
            cmd.parse(["--bar", "zero"], prog="foo")

        self.exit_mock.assert_called_once_with(
            1,
            "argument --bar: invalid int value: 'zero'",
            "usage: foo [--bar BAR]",
        )

    @mock.patch("sys.argv")
    def test_command_error_usage_prog(self, argv_mock):
        argv_mock.__getitem__.return_value = "/usr/bin/foo"

        cmd = commands.Command()
        cmd.add_argument("--bar", required=True)

        with pytest.raises(SystemExit):
            cmd.parse([])
        self.exit_mock.assert_called_once_with(
            mock.ANY,
            mock.ANY,
            "usage: foo --bar BAR",
        )

        self.exit_mock.reset_mock()
        with pytest.raises(SystemExit):
            cmd.parse([], prog="baz")

        self.exit_mock.assert_called_once_with(
            mock.ANY,
            mock.ANY,
            "usage: baz --bar BAR",
        )

    def test_missing_required(self):
        cmd = commands.Command()
        cmd.add_argument("--bar", required=True)

        with pytest.raises(SystemExit):
            cmd.parse([], prog="foo")

        self.exit_mock.assert_called_once_with(
            1,
            "the following arguments are required: --bar",
            "usage: foo --bar BAR",
        )

    def test_missing_positionals(self):
        cmd = commands.Command()
        cmd.add_argument("bar")

        with pytest.raises(SystemExit):
            cmd.parse([], prog="foo")

        assert self.exit_mock.call_count == 1
        assert re.match(
            r"the following arguments are required: bar",
            self.exit_mock.call_args[0][1],
        )

    def test_missing_positionals_subcommand(self):
        child = commands.Command()
        child.add_argument("baz")

        cmd = commands.Command()
        cmd.add_child("bar", child)

        with pytest.raises(SystemExit):
            cmd.parse(["bar"], prog="foo")

        assert self.exit_mock.call_count == 1
        assert re.match(
            r"the following arguments are required: baz",
            self.exit_mock.call_args[0][1],
        )

    def test_unknown_command(self):
        cmd = commands.Command()

        with pytest.raises(SystemExit):
            cmd.parse(["--help"], prog="foo")

        self.exit_mock.assert_called_once_with(
            1,
            "unrecognized arguments: --help",
            "usage: foo",
        )

    def test_invalid_subcommand(self):
        cmd = commands.Command()
        cmd.add_child("baz", commands.Command())

        with pytest.raises(SystemExit):
            cmd.parse(["bar"], prog="foo")

        self.exit_mock.assert_called_once_with(
            1,
            "unrecognized command: bar",
            "usage: foo",
        )

    def test_set(self):
        cmd = commands.Command()
        cmd.set(foo="bar")

        result = cmd.parse([])
        assert result.foo == "bar"

    def test_set_propagate(self):
        child = commands.Command()

        cmd = commands.Command()
        cmd.set(foo="bar")
        cmd.add_child("command", child)

        result = cmd.parse(["command"])
        assert result.foo == "bar"

    def test_innermost_set_wins(self):
        child = commands.Command()
        child.set(foo="bar", baz=1)

        cmd = commands.Command()
        cmd.set(foo="baz", baz=None)
        cmd.add_child("command", child)

        result = cmd.parse(["command"])
        assert result.foo == "bar"
        assert result.baz == 1

    def test_help_action_works(self):
        cmd = commands.Command()
        cmd.add_argument("-h", action="help")
        cmd.format_help = mock.Mock()

        with pytest.raises(SystemExit):
            cmd.parse(["-h"])

        cmd.format_help.assert_called_once_with(mock.ANY)
        self.exit_mock.assert_called_once_with(0, cmd.format_help.return_value)


class UsageTest(unittest.TestCase):
    @mock.patch("sys.argv")
    def test_prog_name_default_and_override(self, argv_mock):
        argv_mock.__getitem__.return_value = "/usr/bin/foo"
        cmd = commands.Command()
        assert cmd.format_usage().strip() == "usage: foo"
        assert cmd.format_usage("baz").strip() == "usage: baz"

    def test_basic_usage(self):
        cmd = commands.Command()
        assert cmd.format_usage("foo").strip() == "usage: foo"

        cmd.add_argument("-h", "--help", action="store_true")
        assert cmd.format_usage("foo").strip() == "usage: foo [-h]"

        cmd.add_argument("bar")
        assert cmd.format_usage("foo").strip() == "usage: foo [-h] bar"

    def test_nested_usage(self):
        child = commands.Command()
        cmd = commands.Command()
        cmd.add_child("bar", child)

        assert cmd.format_usage("foo").strip() == "usage: foo"
        assert cmd.format_usage("foo bar").strip() == "usage: foo bar"

        cmd.add_argument("-h", "--help", action="store_true")
        assert child.format_usage("foo bar").strip() == "usage: foo bar"

        child.add_argument("-h", "--help", action="store_true")
        assert child.format_usage("foo bar").strip() == "usage: foo bar [-h]"


class HelpTest(unittest.TestCase):
    @mock.patch("sys.argv")
    def test_prog_name_default_and_override(self, argv_mock):
        argv_mock.__getitem__.return_value = "/usr/bin/foo"
        cmd = commands.Command()
        assert cmd.format_help().strip() == "usage: foo"
        assert cmd.format_help("bar").strip() == "usage: bar"

    def test_command_without_documentation_or_options(self):
        cmd = commands.Command()
        assert cmd.format_help("bar").strip() == "usage: bar"

    def test_command_with_option(self):
        cmd = commands.Command()
        cmd.add_argument("-h", "--help", action="store_true", help="show this message")

        expected = "usage: foo [-h]\n\nOPTIONS:\n\n  -h, --help  show this message"
        assert expected == cmd.format_help("foo").strip()

    def test_command_with_option_and_positional(self):
        cmd = commands.Command()
        cmd.add_argument("-h", "--help", action="store_true", help="show this message")
        cmd.add_argument("bar", help="some help text")

        expected = (
            "usage: foo [-h] bar\n\n"
            "OPTIONS:\n\n"
            "  -h, --help  show this message\n"
            "  bar         some help text"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_command_with_documentation(self):
        cmd = commands.Command()
        cmd.help = "some text about everything this command does."

        expected = "usage: foo\n\nsome text about everything this command does."
        assert expected == cmd.format_help("foo").strip()

    def test_command_with_documentation_and_option(self):
        cmd = commands.Command()
        cmd.help = "some text about everything this command does."
        cmd.add_argument("-h", "--help", action="store_true", help="show this message")

        expected = (
            "usage: foo [-h]\n\n"
            "some text about everything this command does.\n\n"
            "OPTIONS:\n\n"
            "  -h, --help  show this message"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_subcommand_without_documentation_or_options(self):
        child = commands.Command()
        cmd = commands.Command()
        cmd.add_child("bar", child)

        assert cmd.format_help("foo").strip() == "usage: foo"

    def test_subcommand_with_documentation_shown(self):
        child = commands.Command()
        child.help = "some text about everything this command does."

        cmd = commands.Command()
        cmd.add_child("bar", child)
        expected = (
            "usage: foo\n\n"
            "COMMANDS:\n\n"
            "bar\n\n"
            "  some text about everything this command does."
        )
        assert expected == cmd.format_help("foo").strip()

    def test_subcommand_with_options_shown(self):
        child = commands.Command()
        child.add_argument(
            "-h",
            "--help",
            action="store_true",
            help="show this message",
        )

        cmd = commands.Command()
        cmd.add_child("bar", child)

        expected = (
            "usage: foo\n\nCOMMANDS:\n\nbar [-h]\n\n    -h, --help  show this message"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_subcommand_with_positional_shown(self):
        child = commands.Command()
        child.add_argument("baz", help="the great and wonderful")

        cmd = commands.Command()
        cmd.add_child("bar", child)

        expected = (
            "usage: foo\n\nCOMMANDS:\n\nbar baz\n\n    baz  the great and wonderful"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_subcommand_with_options_and_documentation(self):
        child = commands.Command()
        child.help = "  some text about everything this command does."
        child.add_argument(
            "-h",
            "--help",
            action="store_true",
            help="show this message",
        )

        cmd = commands.Command()
        cmd.add_child("bar", child)

        expected = (
            "usage: foo\n\n"
            "COMMANDS:\n\n"
            "bar [-h]\n\n"
            "  some text about everything this command does.\n\n"
            "    -h, --help  show this message"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_nested_subcommands_with_options(self):
        subchild = commands.Command()
        subchild.add_argument("--test", help="the great and wonderful")

        child = commands.Command()
        child.add_child("baz", subchild)
        child.add_argument(
            "-h",
            "--help",
            action="store_true",
            help="show this message",
        )

        cmd = commands.Command()
        cmd.add_child("bar", child)

        expected = (
            "usage: foo\n\n"
            "COMMANDS:\n\n"
            "bar [-h]\n\n"
            "    -h, --help  show this message\n\n"
            "bar baz [--test TEST]\n\n"
            "    --test TEST  the great and wonderful"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_nested_subcommands_skipped_intermediate(self):
        subchild = commands.Command()
        subchild.add_argument("--test", help="the great and wonderful")

        child = commands.Command()
        child.add_child("baz", subchild)

        cmd = commands.Command()
        cmd.add_child("bar", child)

        expected = (
            "usage: foo\n\n"
            "COMMANDS:\n\n"
            "bar baz [--test TEST]\n\n"
            "    --test TEST  the great and wonderful"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_command_with_option_and_subcommand_with_option(self):
        child = commands.Command()
        child.add_argument("--test", help="the great and wonderful")

        cmd = commands.Command()
        cmd.add_argument("-h", "--help", action="store_true", help="show this message")
        cmd.add_child("bar", child)

        expected = (
            "usage: foo [-h]\n\n"
            "OPTIONS:\n\n"
            "  -h, --help  show this message\n\n"
            "COMMANDS:\n\n"
            "bar [--test TEST]\n\n"
            "    --test TEST  the great and wonderful"
        )
        assert expected == cmd.format_help("foo").strip()

    def test_command_with_options_doc_and_subcommand_with_option_and_doc(self):
        child = commands.Command()
        child.help = "some text about this sub-command."
        child.add_argument("--test", help="the great and wonderful")

        cmd = commands.Command()
        cmd.help = "some text about everything this command does."
        cmd.add_argument("-h", "--help", action="store_true", help="show this message")
        cmd.add_child("bar", child)

        expected = (
            "usage: foo [-h]\n\n"
            "some text about everything this command does.\n\n"
            "OPTIONS:\n\n"
            "  -h, --help  show this message\n\n"
            "COMMANDS:\n\n"
            "bar [--test TEST]\n\n"
            "  some text about this sub-command.\n\n"
            "    --test TEST  the great and wonderful"
        )
        assert expected == cmd.format_help("foo").strip()


class RunTest(unittest.TestCase):
    def test_default_implementation_raises_error(self):
        with pytest.raises(NotImplementedError):
            commands.Command().run(args=None, config=None)


class RootCommandTest(unittest.TestCase):
    def test_config_overrides(self):
        cmd = commands.RootCommand()
        result = cmd.parse(["--option", "foo/bar=baz"])

        assert result.config_overrides[0] == ("foo", "bar", "baz")
