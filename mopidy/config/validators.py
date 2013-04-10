from __future__ import unicode_literals

# TODO: add validate regexp?

def validate_required(value, required):
    """Required validation, normally called in config value's validate() on the
    raw string, _not_ the converted value."""
    if required and not value.strip():
        raise ValueError('must be set.')


def validate_choice(value, choices):
    """Choice validation, normally called in config value's validate()."""
    if choices is not None and value not in choices:
        names = ', '.join(repr(c) for c in choices)
        raise ValueError('must be one of %s, not %s.' % (names, value))


def validate_minimum(value, minimum):
    """Minimum validation, normally called in config value's validate()."""
    if minimum is not None and value < minimum:
        raise ValueError('%r must be larger than %r.' % (value, minimum))


def validate_maximum(value, maximum):
    """Maximum validation, normally called in config value's validate()."""
    if maximum is not None and value > maximum:
        raise ValueError('%r must be smaller than %r.' % (value, maximum))
