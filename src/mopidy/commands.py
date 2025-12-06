from __future__ import annotations

import argparse
import collections
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from mopidy import config as config_lib


def config_files_type(value: str) -> list[str]:
    return value.split(":")


def config_override_type(value: str) -> tuple[str, str, str]:
    try:
        section, remainder = value.split("/", 1)
        key, value = remainder.split("=", 1)
        return (section.strip(), key.strip(), value.strip())
    except ValueError as exc:
        msg = f"{value} must have the format section/key=value"
        raise argparse.ArgumentTypeError(msg) from exc


class _ParserError(Exception):
    def __init__(self, message) -> None:
        self.message = message


class _HelpError(Exception):
    pass


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message) -> NoReturn:
        raise _ParserError(message)


class _HelpAction(argparse.Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str | None = None,
        help: str | None = None,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest or argparse.SUPPRESS,
            default=argparse.SUPPRESS,
            nargs=0,
            help=help,
        )

    def __call__(
        self,
        parser,  # noqa: ARG002
        namespace,  # noqa: ARG002
        values,  # noqa: ARG002
        option_string=None,  # noqa: ARG002
    ) -> NoReturn:
        raise _HelpError


class Command:
    """Command parser and runner for building trees of commands.

    This class provides a wrapper around :class:`argparse.ArgumentParser`
    for handling this type of command line application in a better way than
    argparse's own sub-parser handling.
    """

    help: str | None = None
    #: Help text to display in help output.

    _children: dict[str, Command]
    _arguments: list[tuple[tuple[Any, ...], dict[str, Any]]]
    _overrides: dict[str, Any]

    def __init__(self) -> None:
        self._children = collections.OrderedDict()
        self._arguments = []
        self._overrides = {}

    def _build(self) -> tuple[_ArgumentParser, list[argparse.Action]]:
        actions: list[argparse.Action] = []
        parser = _ArgumentParser(add_help=False)
        parser.register("action", "help", _HelpAction)

        for args, kwargs in self._arguments:
            actions.append(parser.add_argument(*args, **kwargs))

        parser.add_argument("_args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
        return parser, actions

    def add_child(self, name: str, command: Command) -> None:
        """Add a child parser to consider using.

        :param name: name to use for the sub-command that is being added.
        :param command: the command to add.
        """
        self._children[name] = command

    def add_argument(self, *args: Any, **kwargs: Any) -> None:
        """Add an argument to the parser.

        This method takes all the same arguments as the
        :class:`argparse.ArgumentParser` version of this method.
        """
        self._arguments.append((args, kwargs))

    def set(self, **kwargs: Any) -> None:
        """Override a value in the finaly result of parsing."""
        self._overrides.update(kwargs)

    def exit(
        self,
        status_code: int = 0,
        message: str | None = None,
        usage: str | None = None,
    ) -> NoReturn:
        """Optionally print a message and exit."""
        print("\n\n".join(m for m in (usage, message) if m))  # noqa: T201
        sys.exit(status_code)

    def format_usage(self, prog: str | None = None) -> str:
        """Format usage for current parser."""
        actions = self._build()[1]
        prog = prog or Path(sys.argv[0]).name
        return self._usage(actions, prog) + "\n"

    def _usage(self, actions: Iterable[argparse.Action], prog) -> str:
        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])
        return formatter.format_help().strip()

    def format_help(self, prog: str | None = None) -> str:
        """Format help for current parser and children."""
        actions = self._build()[1]
        prog = prog or Path(sys.argv[0]).name

        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])

        if self.help:
            formatter.add_text(self.help)

        if actions:
            formatter.add_text("OPTIONS:")
            formatter.start_section(None)
            formatter.add_arguments(actions)
            formatter.end_section()

        subhelp = []
        for name, child in self._children.items():
            child._subhelp(name, subhelp)

        if subhelp:
            formatter.add_text("COMMANDS:")
            subhelp.insert(0, "")

        return formatter.format_help() + "\n".join(subhelp)

    def _subhelp(self, name: str, result: list[str]) -> None:
        actions = self._build()[1]

        if self.help or actions:
            formatter = argparse.HelpFormatter(name)
            formatter.add_usage(None, actions, [], "")
            formatter.start_section(None)
            formatter.add_text(self.help)
            formatter.start_section(None)
            formatter.add_arguments(actions)
            formatter.end_section()
            formatter.end_section()
            result.append(formatter.format_help())

        for childname, child in self._children.items():
            child._subhelp(f"{name} {childname}", result)

    def parse(self, args: list[str], prog: str | None = None) -> argparse.Namespace:
        """Parse command line arguments.

        Will recursively parse commands until a final parser is found or an
        error occurs. In the case of errors we will print a message and exit.
        Otherwise, any overrides are applied and the current parser stored
        in the command attribute of the return value.

        :param args: list of arguments to parse
        :param prog: name to use for program
        """
        prog = prog or Path(sys.argv[0]).name
        try:
            return self._parse(
                args,
                argparse.Namespace(),
                self._overrides.copy(),
                prog,
            )
        except _HelpError:
            self.exit(0, self.format_help(prog))

    def _parse(
        self,
        args: Sequence[str],
        namespace: argparse.Namespace,
        overrides: dict[str, Any],
        prog: str,
    ) -> argparse.Namespace:
        overrides.update(self._overrides)
        parser, actions = self._build()

        try:
            result = parser.parse_args(args, namespace)
        except _ParserError as exc:
            self.exit(1, str(exc), self._usage(actions, prog))

        if not result._args:
            for attr, value in overrides.items():
                setattr(result, attr, value)
            delattr(result, "_args")
            result.command = self
            return result

        child = result._args.pop(0)
        if child not in self._children:
            usage = self._usage(actions, prog)
            self.exit(1, f"unrecognized command: {child}", usage)

        return self._children[child]._parse(
            result._args,
            result,
            overrides,
            f"{prog} {child}",
        )

    def run(
        self,
        args: argparse.Namespace,
        config: config_lib.Config,
        *_args: Any,
        **_kwargs: Any,
    ) -> int:
        """Run the command.

        Must be implemented by sub-classes that are not simply an intermediate
        in the command namespace.
        """
        raise NotImplementedError
