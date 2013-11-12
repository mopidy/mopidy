import argparse
import collections
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

        if self._children:
            parser.add_argument('_args', nargs=argparse.REMAINDER)
        else:
            parser.set_defaults(_args=[])

        return parser, actions

    def add_child(self, name, command):
        self._children[name] = command

    def add_argument(self, *args, **kwargs):
        self._arguments.append((args, kwargs))

    def format_usage(self, prog=None):
        actions = self._build()[1]
        formatter = argparse.HelpFormatter(prog or sys.argv[0])
        formatter.add_usage(None, actions, [])
        return formatter.format_help()

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
