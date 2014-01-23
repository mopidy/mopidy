"""
This is Mopidy's MPD protocol implementation.

This is partly based upon the `MPD protocol documentation
<http://www.musicpd.org/doc/protocol/>`_, which is a useful resource, but it is
rather incomplete with regards to data formats, both for requests and
responses. Thus, we have had to talk a great deal with the the original `MPD
server <http://mpd.wikia.com/>`_ using telnet to get the details we need to
implement our own MPD server which is compatible with the numerous existing
`MPD clients <http://mpd.wikia.com/wiki/Clients>`_.
"""

from __future__ import unicode_literals

import collections
import inspect
import re

from mopidy.utils import formatting

#: The MPD protocol uses UTF-8 for encoding all data.
ENCODING = 'UTF-8'

#: The MPD protocol uses ``\n`` as line terminator.
LINE_TERMINATOR = '\n'

#: The MPD protocol version is 0.17.0.
VERSION = '0.17.0'

MpdCommand = collections.namedtuple('MpdCommand', ['name', 'auth_required'])

#: Set of all available commands, represented as :class:`MpdCommand` objects.
mpd_commands = set()

#: Map between request matchers and request handler functions.
request_handlers = {}


def handle_request(pattern, auth_required=True):
    """
    Decorator for connecting command handlers to command requests.

    If you use named groups in the pattern, the decorated method will get the
    groups as keyword arguments. If the group is optional, remember to give the
    argument a default value.

    For example, if the command is ``do that thing`` the ``what`` argument will
    be ``this thing``::

        @handle_request('do\ (?P<what>.+)$')
        def do(what):
            ...

    Note that the patterns are compiled with the :attr:`re.VERBOSE` flag. Thus,
    you must escape any space characters you want to match, but you're also
    free to add non-escaped whitespace to format the pattern for easier
    reading.

    :param pattern: regexp pattern for matching commands
    :type pattern: string
    """
    def decorator(func):
        match = re.search('([a-z_]+)', pattern)
        if match is not None:
            mpd_commands.add(
                MpdCommand(name=match.group(), auth_required=auth_required))
        compiled_pattern = re.compile(pattern, flags=(re.UNICODE | re.VERBOSE))
        if compiled_pattern in request_handlers:
            raise ValueError('Tried to redefine handler for %s with %s' % (
                pattern, func))
        request_handlers[compiled_pattern] = func
        func.__doc__ = """
    *Pattern:*

    .. code-block:: text

%(pattern)s

%(docs)s
        """ % {
            'pattern': formatting.indent(pattern, places=8, singles=True),
            'docs': func.__doc__ or '',
        }
        return func
    return decorator


def load_protocol_modules():
    """
    The protocol modules must be imported to get them registered in
    :attr:`request_handlers` and :attr:`mpd_commands`.
    """
    from . import (  # noqa
        audio_output, channels, command_list, connection, current_playlist,
        empty, music_db, playback, reflection, status, stickers,
        stored_playlists)


def INT(value):
    if value is None:
        raise ValueError('None is not a valid integer')
    # TODO: check for whitespace via value != value.strip()?
    return int(value)


def UINT(value):
    if value is None:
        raise ValueError('None is not a valid integer')
    if not value.isdigit():
        raise ValueError('Only positive numbers are allowed')
    return int(value)


def BOOL(value):
    if value in ('1', '0'):
        return bool(int(value))
    raise ValueError('%r is not 0 or 1' % value)


def RANGE(value):
    # TODO: test and check that values are positive
    if ':' in value:
        start, stop = value.split(':', 1)
        start = UINT(start)
        if stop.strip():
            stop = UINT(stop)
            if start >= stop:
                raise ValueError('End must be larger than start')
        else:
            stop = None
    else:
        start = UINT(value)
        stop = start + 1
    return slice(start, stop)


class Commands(object):
    def __init__(self):
        self.handlers = {}

    def add(self, name, auth_required=True, list_command=True, **validators):
        def wrapper(func):
            if name in self.handlers:
                raise Exception('%s already registered' % name)

            args, varargs, keywords, defaults = inspect.getargspec(func)
            defaults = dict(zip(args[-len(defaults or []):], defaults or []))

            if not args and not varargs:
                raise TypeError('Handler must accept at least one argument.')

            if len(args) > 1 and varargs:
                raise TypeError(
                    '*args may not be combined with regular argmuments')

            if not set(validators.keys()).issubset(args):
                raise TypeError('Validator for non-existent arg passed')

            if keywords:
                raise TypeError('**kwargs are not permitted')

            def validate(*args, **kwargs):
                if varargs:
                    return func(*args, **kwargs)
                callargs = inspect.getcallargs(func, *args, **kwargs)
                for key, value in callargs.items():
                    default = defaults.get(key, object())
                    if key in validators and value != default:
                        callargs[key] = validators[key](value)
                return func(**callargs)

            validate.auth_required = auth_required
            validate.list_command = list_command
            self.handlers[name] = validate
            return func
        return wrapper

    def call(self, args, context=None):
        if not args:
            raise TypeError('No args provided')
        if args[0] not in self.handlers:
            raise LookupError('Unknown command')
        return self.handlers[args[0]](context, *args[1:])


#: Global instance to install commands into
commands = Commands()
