from __future__ import unicode_literals


def validate_choice(value, choices):
    """Choice validation, normally called in config value's validate()."""
    if choices is not None and value not in choices :
        raise ValueError('must be one of %s.' % ', '.join(choices))


def validate_minimum(value, minimum):
    """Minimum validation, normally called in config value's validate()."""
    if minimum is not None and value < minimum:
        raise ValueError('must be larger than %s.' % minimum)


def validate_maximum(value, maximum):
    """Maximum validation, normally called in config value's validate()."""
    if maximum is not None and value > maximum:
        raise ValueError('must be smaller than %s.' % maximum)
