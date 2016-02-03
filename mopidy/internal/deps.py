from __future__ import absolute_import, unicode_literals

import functools
import os
import platform
import sys

import pkg_resources

from mopidy.internal import formatting
from mopidy.internal.gi import Gst, gi


def format_dependency_list(adapters=None):
    if adapters is None:
        dist_names = set([
            ep.dist.project_name for ep in
            pkg_resources.iter_entry_points('mopidy.ext')
            if ep.dist.project_name != 'Mopidy'])
        dist_infos = [
            functools.partial(pkg_info, dist_name)
            for dist_name in dist_names]

        adapters = [
            executable_info,
            platform_info,
            python_info,
            functools.partial(pkg_info, 'Mopidy', True)
        ] + dist_infos + [
            gstreamer_info,
        ]

    return '\n'.join([_format_dependency(a()) for a in adapters])


def _format_dependency(dep_info):
    lines = []

    if 'version' not in dep_info:
        lines.append('%s: not found' % dep_info['name'])
    else:
        if 'path' in dep_info:
            source = ' from %s' % dep_info['path']
        else:
            source = ''
        lines.append('%s: %s%s' % (
            dep_info['name'],
            dep_info['version'],
            source,
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


def executable_info():
    return {
        'name': 'Executable',
        'version': sys.argv[0],
    }


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
        'path': os.path.dirname(platform.__file__),
    }


def pkg_info(project_name=None, include_extras=False):
    if project_name is None:
        project_name = 'Mopidy'
    try:
        distribution = pkg_resources.get_distribution(project_name)
        extras = include_extras and distribution.extras or []
        dependencies = [
            pkg_info(d) for d in distribution.requires(extras)]
        return {
            'name': project_name,
            'version': distribution.version,
            'path': distribution.location,
            'dependencies': dependencies,
        }
    except pkg_resources.ResolutionError:
        return {
            'name': project_name,
        }


def gstreamer_info():
    other = []
    other.append('Python wrapper: python-gi %s' % gi.__version__)

    found_elements = []
    missing_elements = []
    for name, status in _gstreamer_check_elements():
        if status:
            found_elements.append(name)
        else:
            missing_elements.append(name)

    other.append('Relevant elements:')
    other.append('  Found:')
    for element in found_elements:
        other.append('    %s' % element)
    if not found_elements:
        other.append('    none')
    other.append('  Not found:')
    for element in missing_elements:
        other.append('    %s' % element)
    if not missing_elements:
        other.append('    none')

    return {
        'name': 'GStreamer',
        'version': '.'.join(map(str, Gst.version())),
        'path': os.path.dirname(gi.__file__),
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

        # Audio sinks
        'alsasink',
        'osssink',
        'oss4sink',
        'pulsesink',

        # MP3 encoding and decoding
        #
        # One of flump3dec, mad, and mpg123audiodec is required for MP3
        # playback.
        'flump3dec',
        'id3demux',
        'id3v2mux',
        'lamemp3enc',
        'mad',
        'mpegaudioparse',
        'mpg123audiodec',

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
        Gst.Registry.get().get_feature_list(Gst.ElementFactory)]
    return [
        (element, element in known_elements) for element in elements_to_check]
