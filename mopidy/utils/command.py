import argparse
import collections


class CommandError(Exception):
    pass


class Command(object):
    def __init__(self):
        self._children = collections.OrderedDict()
        self._arguments = []

    def _build_parser(self):
        parser = argparse.ArgumentParser(add_help=False)

        for args, kwargs in self._arguments:
            parser.add_argument(*args, **kwargs)

        if self._children:
            parser.add_argument('_args', nargs=argparse.REMAINDER)
        else:
            parser.set_defaults(_args=[])

        return parser

    def add_child(self, name, command):
        self._children[name] = command

    def add_argument(self, *args, **kwargs):
        self._arguments.append((args, kwargs))

    def parse(self, args, namespace=None):
        if not namespace:
            namespace = argparse.Namespace()

        parser = self._build_parser()
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
