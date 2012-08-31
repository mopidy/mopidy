import os
import sys

import pygst
pygst.require('0.10')
import gst

import pykka

from mopidy.utils.log import indent


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
            gstreamer_info,
            pykka_info,
            pyspotify_info,
            pylast_info,
        ]

    lines = []
    for adapter in adapters:
        dep_info = adapter()
        lines.append('%(name)s: %(version)s' % {
            'name': dep_info['name'],
            'version': dep_info.get('version', 'not found'),
        })
        if 'path' in dep_info:
            lines.append('  Imported from: %s' % (
                os.path.dirname(dep_info['path'])))
        if 'other' in dep_info:
            lines.append('  Other: %s' % (
                indent(dep_info['other'])),)
    return '\n'.join(lines)


def gstreamer_info():
    return {
        'name': 'Gstreamer',
        'version': '.'.join(map(str, gst.get_gst_version())),
        'path': gst.__file__,
        'other': 'Python wrapper: gst-python %s' % (
            '.'.join(map(str, gst.get_pygst_version()))),
    }


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


def pyspotify_info():
    dep_info = {'name': 'pyspotify'}
    try:
        import spotify
        if hasattr(spotify, '__version__'):
            dep_info['version'] = spotify.__version__
        else:
            dep_info['version'] = '< 1.3'
        dep_info['path'] = spotify.__file__
        dep_info['other'] = 'Built for libspotify API version %d' % (
            spotify.api_version,)
    except ImportError:
        pass
    return dep_info


def pylast_info():
    dep_info = {'name': 'pylast'}
    try:
        import pylast
        dep_info['version'] = pylast.__version__
        dep_info['path'] = pylast.__file__
    except ImportError:
        pass
    return dep_info
