from __future__ import absolute_import, unicode_literals

# TODO: add validate regexp?


def validate_required(value, required):
    """Validate that ``value`` is set if ``required``

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize` on
    the raw string, _not_ the converted value.
    """
    if required and not value:
        raise ValueError('must be set.')


def validate_choice(value, choices):
    """Validate that ``value`` is one of the ``choices``

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize`.
    """
    if choices is not None and value not in choices:
        names = ', '.join(repr(c) for c in choices)
        raise ValueError('must be one of %s, not %s.' % (names, value))


def validate_minimum(value, minimum):
    """Validate that ``value`` is at least ``minimum``

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize`.
    """
    if minimum is not None and value < minimum:
        raise ValueError('%r must be larger than %r.' % (value, minimum))


def validate_maximum(value, maximum):
    """Validate that ``value`` is at most ``maximum``

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize`.
    """
    if maximum is not None and value > maximum:
        raise ValueError('%r must be smaller than %r.' % (value, maximum))
