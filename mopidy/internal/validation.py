from __future__ import absolute_import, unicode_literals

import collections

from mopidy import compat, exceptions
from mopidy.compat import urllib

PLAYBACK_STATES = {'paused', 'stopped', 'playing'}

SEARCH_FIELDS = {
    'uri', 'track_name', 'album', 'artist', 'albumartist', 'composer',
    'performer', 'track_no', 'genre', 'date', 'comment', 'any'}

PLAYLIST_FIELDS = {'uri', 'name'}  # TODO: add length and last_modified?

TRACKLIST_FIELDS = {  # TODO: add bitrate, length, disc_no, track_no, modified?
    'uri', 'name', 'genre', 'date', 'comment', 'musicbrainz_id'}

DISTINCT_FIELDS = {
    'track', 'artist', 'albumartist', 'album', 'composer', 'performer', 'date',
    'genre'}


# TODO: _check_iterable(check, msg, **kwargs) + [check(a) for a in arg]?
def _check_iterable(arg, msg, **kwargs):
    """Ensure we have an iterable which is not a string or an iterator"""
    if isinstance(arg, compat.string_types):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))
    elif not isinstance(arg, collections.Iterable):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))
    elif iter(arg) is iter(arg):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))


def check_choice(arg, choices, msg='Expected one of {choices}, not {arg!r}'):
    if arg not in choices:
        raise exceptions.ValidationError(msg.format(
            arg=arg, choices=tuple(choices)))


def check_boolean(arg, msg='Expected a boolean, not {arg!r}'):
    check_instance(arg, bool, msg=msg)


def check_instance(arg, cls, msg='Expected a {name} instance, not {arg!r}'):
    if not isinstance(arg, cls):
        raise exceptions.ValidationError(
            msg.format(arg=arg, name=cls.__name__))


def check_instances(arg, cls, msg='Expected a list of {name}, not {arg!r}'):
    _check_iterable(arg, msg, name=cls.__name__)
    if not all(isinstance(instance, cls) for instance in arg):
        raise exceptions.ValidationError(
            msg.format(arg=arg, name=cls.__name__))


def check_integer(arg, min=None, max=None):
    if not isinstance(arg, compat.integer_types):
        raise exceptions.ValidationError('Expected an integer, not %r' % arg)
    elif min is not None and arg < min:
        raise exceptions.ValidationError(
            'Expected number larger or equal to %d, not %r' % (min, arg))
    elif max is not None and arg > max:
        raise exceptions.ValidationError(
            'Expected number smaller or equal to %d, not %r' % (max, arg))


def check_query(arg, fields=SEARCH_FIELDS, list_values=True):
    # TODO: normalize name  -> track_name
    # TODO: normalize value -> [value]
    # TODO: normalize blank -> [] or just remove field?
    # TODO: remove list_values?

    if not isinstance(arg, collections.Mapping):
        raise exceptions.ValidationError(
            'Expected a query dictionary, not {arg!r}'.format(arg=arg))

    for key, value in arg.items():
        check_choice(key, fields, msg='Expected query field to be one of '
                     '{choices}, not {arg!r}')
        if list_values:
            msg = 'Expected "{key}" to be list of strings, not {arg!r}'
            _check_iterable(value, msg, key=key)
            [_check_query_value(key, v, msg) for v in value]
        else:
            _check_query_value(
                key, value, 'Expected "{key}" to be a string, not {arg!r}')


def _check_query_value(key, arg, msg):
    if not isinstance(arg, compat.string_types) or not arg.strip():
        raise exceptions.ValidationError(msg.format(arg=arg, key=key))


def check_uri(arg, msg='Expected a valid URI, not {arg!r}'):
    if not isinstance(arg, compat.string_types):
        raise exceptions.ValidationError(msg.format(arg=arg))
    elif urllib.parse.urlparse(arg).scheme == '':
        raise exceptions.ValidationError(msg.format(arg=arg))


def check_uris(arg, msg='Expected a list of URIs, not {arg!r}'):
    _check_iterable(arg, msg)
    [check_uri(a, msg) for a in arg]
