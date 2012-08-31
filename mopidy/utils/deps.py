import sys

import pykka


def list_deps_optparse_callback(*args):
    """
    Prints a list of all dependencies.

    Called by optparse when Mopidy is run with the :option:`--list-deps`
    option.
    """
    print format_dependency_list()
    sys.exit(0)


def format_dependency_list(adapters=None):
    if adapters is None:
        adapters = [
            pykka_info,
        ]

    lines = []
    for adapter in adapters:
        dep_info = adapter()
        lines.append('%(name)s: %(version)s' % dep_info)
        if 'path' in dep_info:
            lines.append('  Imported from: %(path)s' % dep_info)
    return '\n'.join(lines)


def pykka_info():
    if hasattr(pykka, '__version__'):
        # Pykka >= 0.14
        version = pykka.__version__
    else:
        # Pykka < 0.14
        version = pykka.get_version()
    return {
        'name': 'Pykka',
        'version': version,
        'path': pykka.__file__,
    }
