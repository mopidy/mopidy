import argparse
import collections
import os
import sys


class CommandError(Exception):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CommandError(message)


class Command(object):
    def __init__(self):
        self._children = collections.OrderedDict()
        self._arguments = []

    def _build(self):
        actions = []
        parser = ArgumentParser(add_help=False)

        for args, kwargs in self._arguments:
            actions.append(parser.add_argument(*args, **kwargs))

        parser.add_argument('_args', nargs=argparse.REMAINDER,
                            help=argparse.SUPPRESS)
        return parser, actions

    def add_child(self, name, command):
        self._children[name] = command

    def add_argument(self, *args, **kwargs):
        self._arguments.append((args, kwargs))

    def format_usage(self, prog=None):
        actions = self._build()[1]
        prog = prog or os.path.basename(sys.argv[0])
        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])
        return formatter.format_help()

    def format_help(self, prog=None):
        actions = self._build()[1]
        prog = prog or os.path.basename(sys.argv[0])

        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])

        if self.__doc__:
            formatter.add_text(self.__doc__)

        if actions:
            formatter.add_text('OPTIONS:')
            formatter.start_section(None)
            formatter.add_arguments(actions)
            formatter.end_section()

        subhelp = []
        for name, child in self._children.items():
            child._subhelp(name, subhelp)

        if subhelp:
            formatter.add_text('COMMANDS:')
            subhelp.insert(0, '')

        return formatter.format_help() + '\n'.join(subhelp)

    def _subhelp(self, name, result):
        actions = self._build()[1]

        if self.__doc__ or actions:
            formatter = argparse.HelpFormatter(name)
            formatter.add_usage(None, actions, [], '')
            formatter.start_section(None)
            formatter.add_text(self.__doc__)
            formatter.start_section(None)
            formatter.add_arguments(actions)
            formatter.end_section()
            formatter.end_section()
            result.append(formatter.format_help())

        for childname, child in self._children.items():
            child._subhelp(' '.join((name, childname)), result)

    def parse(self, args, namespace=None):
        if not namespace:
            namespace = argparse.Namespace()

        parser = self._build()[0]
        result, unknown = parser.parse_known_args(args, namespace)

        if unknown:
            raise CommandError('Unknown command options.')

        args = result._args
        delattr(result, '_args')

        if not args:
            result.command = self
            return result

        if args[0] not in self._children:
            raise CommandError('Invalid sub-command provided.')

        return self._children[args[0]].parse(args[1:], result)
