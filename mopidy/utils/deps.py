import os
import platform
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
            platform_info,
            python_info,
            gstreamer_info,
            pykka_info,
            pyspotify_info,
            pylast_info,
            dbus_info,
            serial_info,
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


def platform_info():
    return {
        'name': 'Platform',
        'version': platform.platform(),
    }


def python_info():
    return {
        'name': 'Python',
        'version': '%s %s' % (platform.python_implementation(),
            platform.python_version()),
        'path': platform.__file__,
    }


def gstreamer_info():
    other = []
    other.append('Python wrapper: gst-python %s' % (
        '.'.join(map(str, gst.get_pygst_version()))))
    other.append('Relevant elements:')
    for name, status in _gstreamer_check_elements():
        other.append('  %s: %s' % (name, 'OK' if status else 'not found'))
    return {
        'name': 'GStreamer',
        'version': '.'.join(map(str, gst.get_gst_version())),
        'path': gst.__file__,
        'other': '\n'.join(other),
    }


def _gstreamer_check_elements():
    elements_to_check = [
        # Core playback
        'uridecodebin',

        # External HTTP streams
        'souphttpsrc',

        # Spotify
        'appsrc',

        # Mixers and sinks
        'alsamixer',
        'alsasink',
        'ossmixer',
        'osssink',
        'oss4mixer',
        'oss4sink',
        'pulsemixer',
        'pulsesink',

        # MP3 encoding and decoding
        'mp3parse',
        'mad',
        'id3demux',
        'id3v2mux',
        'lame',

        # Ogg Vorbis encoding and decoding
        'vorbisdec',
        'vorbisenc',
        'vorbisparse',
        'oggdemux',
        'oggmux',
        'oggparse',

        # Flac decoding
        'flacdec',
        'flacparse',

        # Shoutcast output
        'shout2send',
    ]
    known_elements = [factory.get_name() for factory in
        gst.registry_get_default().get_feature_list(gst.TYPE_ELEMENT_FACTORY)]
    return [(element, element in known_elements) for element in elements_to_check]


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


def dbus_info():
    dep_info = {'name': 'dbus-python'}
    try:
        import dbus
        dep_info['version'] = dbus.__version__
        dep_info['path'] = dbus.__file__
    except ImportError:
        pass
    return dep_info


def serial_info():
    dep_info = {'name': 'pyserial'}
    try:
        import serial
        dep_info['version'] = serial.VERSION
        dep_info['path'] = serial.__file__
    except ImportError:
        pass
    return dep_info
