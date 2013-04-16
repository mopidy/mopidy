from __future__ import unicode_literals

import functools
import os
import platform
import sys

import pygst
pygst.require('0.10')
import gst

import pkg_resources

from . import formatting


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
            functools.partial(pkg_info, 'Mopidy', True),
        ]

        dist_names = set([
            ep.dist.project_name for ep in
            pkg_resources.iter_entry_points('mopidy.ext')
            if ep.dist.project_name != 'Mopidy'])
        for dist_name in dist_names:
            adapters.append(
                functools.partial(pkg_info, dist_name))

    return '\n'.join([_format_dependency(a()) for a in adapters])


def _format_dependency(dep_info):
    lines = []

    if 'version' not in dep_info:
        lines.append('%s: not found' % dep_info['name'])
    else:
        lines.append('%s: %s from %s' % (
            dep_info['name'],
            dep_info['version'],
            os.path.dirname(dep_info.get('path', 'none')),
        ))

    if 'other' in dep_info:
        lines.append('  Detailed information: %s' % (
            formatting.indent(dep_info['other'], places=4)),)

    if dep_info.get('dependencies', []):
        for sub_dep_info in dep_info['dependencies']:
            sub_dep_lines = _format_dependency(sub_dep_info)
            lines.append(
                formatting.indent(sub_dep_lines, places=2, singles=True))

    return '\n'.join(lines)


def platform_info():
    return {
        'name': 'Platform',
        'version': platform.platform(),
    }


def python_info():
    return {
        'name': 'Python',
        'version': '%s %s' % (
            platform.python_implementation(), platform.python_version()),
        'path': platform.__file__,
    }


def pkg_info(project_name=None, include_extras=False):
    if project_name is None:
        project_name = 'Mopidy'
    distribution = pkg_resources.get_distribution(project_name)
    extras = include_extras and distribution.extras or []
    dependencies = [
        pkg_info(d) for d in distribution.requires(extras)]
    return {
        'name': distribution.project_name,
        'version': distribution.version,
        'path': distribution.location,
        'dependencies': dependencies,
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
    known_elements = [
        factory.get_name() for factory in
        gst.registry_get_default().get_feature_list(gst.TYPE_ELEMENT_FACTORY)]
    return [
        (element, element in known_elements) for element in elements_to_check]
