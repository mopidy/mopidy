from __future__ import unicode_literals

import argparse

from mopidy.utils import versioning


def config_files_type(value):
    return value.split(b':')


def config_override_type(value):
    try:
        section, remainder = value.split(b'/', 1)
        key, value = remainder.split(b'=', 1)
        return (section.strip(), key.strip(), value.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(
            '%s must have the format section/key=value' % value)


def build_parser():
    parser = argparse.ArgumentParser()
    parser.set_defaults(verbosity_level=0)
    parser.add_argument(
        '--version', action='version',
        version='Mopidy %s' % versioning.get_version())
    parser.add_argument(
        '-q', '--quiet',
        action='store_const', const=-1, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_argument(
        '-v', '--verbose',
        action='count', dest='verbosity_level',
        help='more output (debug level)')
    parser.add_argument(
        '--save-debug-log',
        action='store_true', dest='save_debug_log',
        help='save debug log to "./mopidy.log"')
    parser.add_argument(
        '--config',
        action='store', dest='config_files', type=config_files_type,
        default=b'$XDG_CONFIG_DIR/mopidy/mopidy.conf',
        help='config files to use, colon seperated, later files override')
    parser.add_argument(
        '-o', '--option',
        action='append', dest='config_overrides', type=config_override_type,
        help='`section/key=value` values to override config options')

    subparser = parser.add_subparsers(
        title='commands', metavar='COMMAND', dest='command')

    subparser.add_parser('run', help='start mopidy server')
    subparser.add_parser('config', help='show current config')
    subparser.add_parser('deps', help='show dependencies')

    return parser, subparser
