from __future__ import unicode_literals


def deprecated_property(
        getter=None, setter=None, message='Property is deprecated'):

    # During development, this is a convenient place to add logging, emit
    # warnings, or ``assert False`` to ensure you are not using any of the
    # deprecated properties.
    #
    # Using inspect to find the call sites to emit proper warnings makes
    # parallel execution of our test suite slower than serial execution. Thus,
    # we don't want to add any extra overhead here by default.

    return property(getter, setter)
