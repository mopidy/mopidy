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

from __future__ import absolute_import, unicode_literals

import inspect

from mopidy.mpd import exceptions

#: The MPD protocol uses UTF-8 for encoding all data.
ENCODING = 'UTF-8'

#: The MPD protocol uses ``\n`` as line terminator.
LINE_TERMINATOR = '\n'

#: The MPD protocol version is 0.19.0.
VERSION = '0.19.0'


def load_protocol_modules():
    """
    The protocol modules must be imported to get them registered in
    :attr:`commands`.
    """
    from . import (  # noqa
        audio_output, channels, command_list, connection, current_playlist,
        mount, music_db, playback, reflection, status, stickers,
        stored_playlists)


def INT(value):  # noqa: N802
    """Converts a value that matches [+-]?\d+ into and integer."""
    if value is None:
        raise ValueError('None is not a valid integer')
    # TODO: check for whitespace via value != value.strip()?
    return int(value)


def UINT(value):  # noqa: N802
    """Converts a value that matches \d+ into an integer."""
    if value is None:
        raise ValueError('None is not a valid integer')
    if not value.isdigit():
        raise ValueError('Only positive numbers are allowed')
    return int(value)


def BOOL(value):  # noqa: N802
    """Convert the values 0 and 1 into booleans."""
    if value in ('1', '0'):
        return bool(int(value))
    raise ValueError('%r is not 0 or 1' % value)


def RANGE(value):  # noqa: N802
    """Convert a single integer or range spec into a slice

    ``n`` should become ``slice(n, n+1)``
    ``n:`` should become ``slice(n, None)``
    ``n:m`` should become ``slice(n, m)`` and ``m > n`` must hold
    """
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

    """Collection of MPD commands to expose to users.

    Normally used through the global instance which command handlers have been
    installed into.
    """

    def __init__(self):
        self.handlers = {}

    # TODO: consider removing auth_required and list_command in favour of
    # additional command instances to register in?
    def add(self, name, auth_required=True, list_command=True, **validators):
        """Create a decorator that registers a handler and validation rules.

        Additional keyword arguments are treated as converters/validators to
        apply to tokens converting them to proper Python types.

        Requirements for valid handlers:

        - must accept a context argument as the first arg.
        - may not use variable keyword arguments, ``**kwargs``.
        - may use variable arguments ``*args`` *or* a mix of required and
          optional arguments.

        Decorator returns the unwrapped function so that tests etc can use the
        functions with values with correct python types instead of strings.

        :param string name: Name of the command being registered.
        :param bool auth_required: If authorization is required.
        :param bool list_command: If command should be listed in reflection.
        """

        def wrapper(func):
            if name in self.handlers:
                raise ValueError('%s already registered' % name)

            args, varargs, keywords, defaults = inspect.getargspec(func)
            defaults = dict(zip(args[-len(defaults or []):], defaults or []))

            if not args and not varargs:
                raise TypeError('Handler must accept at least one argument.')

            if len(args) > 1 and varargs:
                raise TypeError(
                    '*args may not be combined with regular arguments')

            if not set(validators.keys()).issubset(args):
                raise TypeError('Validator for non-existent arg passed')

            if keywords:
                raise TypeError('**kwargs are not permitted')

            def validate(*args, **kwargs):
                if varargs:
                    return func(*args, **kwargs)

                try:
                    callargs = inspect.getcallargs(func, *args, **kwargs)
                except TypeError:
                    raise exceptions.MpdArgError(
                        'wrong number of arguments for "%s"' % name)

                for key, value in callargs.items():
                    default = defaults.get(key, object())
                    if key in validators and value != default:
                        try:
                            callargs[key] = validators[key](value)
                        except ValueError:
                            raise exceptions.MpdArgError('incorrect arguments')

                return func(**callargs)

            validate.auth_required = auth_required
            validate.list_command = list_command
            self.handlers[name] = validate
            return func
        return wrapper

    def call(self, tokens, context=None):
        """Find and run the handler registered for the given command.

        If the handler was registered with any converters/validators they will
        be run before calling the real handler.

        :param list tokens: List of tokens to process
        :param context: MPD context.
        :type context: :class:`~mopidy.mpd.dispatcher.MpdContext`
        """
        if not tokens:
            raise exceptions.MpdNoCommand()
        if tokens[0] not in self.handlers:
            raise exceptions.MpdUnknownCommand(command=tokens[0])
        return self.handlers[tokens[0]](context, *tokens[1:])


#: Global instance to install commands into
commands = Commands()
