import argparse
import collections
import os
import sys


class CommandError(Exception):
    def __init__(self, message, usage=None):
        self.message = message
        self.usage = usage

    def __str__(self):
        return '%s\n\nerror: %s' % (self.usage, self.message)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CommandError(message)


class Command(object):
    def __init__(self):
        self._children = collections.OrderedDict()
        self._arguments = []
        self._defaults = {}

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

    def set_defaults(self, **kwargs):
        self._defaults.update(kwargs)

    def format_usage(self, prog=None):
        actions = self._build()[1]
        prog = prog or os.path.basename(sys.argv[0])
        return self._usage(actions, prog) + '\n'

    def _usage(self, actions, prog):
        formatter = argparse.HelpFormatter(prog)
        formatter.add_usage(None, actions, [])
        return formatter.format_help().strip()

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

    def parse(self, args, prog=None):
        prog = prog or os.path.basename(sys.argv[0])
        return self._parse(
            args, argparse.Namespace(), self._defaults.copy(), prog)

    def _parse(self, args, namespace, defaults, prog):
        defaults.update(self._defaults)
        parser, actions = self._build()

        try:
            result = parser.parse_args(args, namespace)
        except CommandError as e:
            e.usage = self._usage(actions, prog)
            raise

        if not result._args:
            for attr, value in defaults.items():
                if not hasattr(result, attr):
                    setattr(result, attr, value)
            delattr(result, '_args')
            result.command = self
            return result

        child = result._args.pop(0)
        if child not in self._children:
            raise CommandError('unrecognized command: %s' % child,
                               usage=self._usage(actions, prog))

        return self._children[child]._parse(
            result._args, result, defaults, ' '.join([prog, child]))

    def run(self, *args, **kwargs):
        raise NotImplementedError
