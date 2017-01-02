from __future__ import absolute_import, unicode_literals

import io
import itertools
import logging
import os.path
import re

from mopidy import compat
from mopidy.compat import configparser
from mopidy.config import keyring
from mopidy.config.schemas import *
from mopidy.config.types import *
from mopidy.internal import path, versioning

logger = logging.getLogger(__name__)

# flake8: noqa:
# TODO: Update this to be flake8 compliant

_core_schema = ConfigSchema('core')
_core_schema['cache_dir'] = Path()
_core_schema['config_dir'] = Path()
_core_schema['data_dir'] = Path()
# MPD supports at most 10k tracks, some clients segfault when this is exceeded.
_core_schema['max_tracklist_length'] = Integer(minimum=1, maximum=10000)
_core_schema['restore_state'] = Boolean(optional=True)

_logging_schema = ConfigSchema('logging')
_logging_schema['color'] = Boolean()
_logging_schema['console_format'] = String()
_logging_schema['debug_format'] = String()
_logging_schema['debug_file'] = Path()
_logging_schema['config_file'] = Path(optional=True)

_loglevels_schema = MapConfigSchema('loglevels', LogLevel())
_logcolors_schema = MapConfigSchema('logcolors', LogColor())

_audio_schema = ConfigSchema('audio')
_audio_schema['mixer'] = String()
_audio_schema['mixer_track'] = Deprecated()
_audio_schema['mixer_volume'] = Integer(optional=True, minimum=0, maximum=100)
_audio_schema['output'] = String()
_audio_schema['visualizer'] = Deprecated()
_audio_schema['buffer_time'] = Integer(optional=True, minimum=1)

_proxy_schema = ConfigSchema('proxy')
_proxy_schema['scheme'] = String(optional=True,
                                 choices=['http', 'https', 'socks4', 'socks5'])
_proxy_schema['hostname'] = Hostname(optional=True)
_proxy_schema['port'] = Port(optional=True)
_proxy_schema['username'] = String(optional=True)
_proxy_schema['password'] = Secret(optional=True)

# NOTE: if multiple outputs ever comes something like LogLevelConfigSchema
# _outputs_schema = config.AudioOutputConfigSchema()

_schemas = [
    _core_schema, _logging_schema, _loglevels_schema, _logcolors_schema,
    _audio_schema, _proxy_schema]

_INITIAL_HELP = """
# For further information about options in this file see:
#   http://docs.mopidy.com/
#
# The initial commented out values reflect the defaults as of:
#   %(versions)s
#
# Available options and defaults might have changed since then,
# run `mopidy config` to see the current effective config and
# `mopidy --version` to check the current version.
"""


def read(config_file):
    """Helper to load config defaults in same way across core and extensions"""
    with io.open(config_file, 'rb') as filehandle:
        return filehandle.read()


def load(files, ext_schemas, ext_defaults, overrides):
    config_dir = os.path.dirname(__file__)
    defaults = [read(os.path.join(config_dir, 'default.conf'))]
    defaults.extend(ext_defaults)
    raw_config = _load(files, defaults, keyring.fetch() + (overrides or []))

    schemas = _schemas[:]
    schemas.extend(ext_schemas)
    return _validate(raw_config, schemas)


def format(config, ext_schemas, comments=None, display=True):
    schemas = _schemas[:]
    schemas.extend(ext_schemas)
    return _format(config, comments or {}, schemas, display, False)


def format_initial(extensions_data):
    config_dir = os.path.dirname(__file__)
    defaults = [read(os.path.join(config_dir, 'default.conf'))]
    defaults.extend(d.extension.get_default_config() for d in extensions_data)
    raw_config = _load([], defaults, [])

    schemas = _schemas[:]
    schemas.extend(d.extension.get_config_schema() for d in extensions_data)

    config, errors = _validate(raw_config, schemas)

    versions = ['Mopidy %s' % versioning.get_version()]
    extensions_data = sorted(
        extensions_data, key=lambda d: d.extension.dist_name)
    for data in extensions_data:
        versions.append('%s %s' % (
            data.extension.dist_name, data.extension.version))

    header = _INITIAL_HELP.strip() % {'versions': '\n#   '.join(versions)}
    formatted_config = _format(
        config=config, comments={}, schemas=schemas,
        display=False, disable=True).decode('utf-8')
    return header + '\n\n' + formatted_config


def _load(files, defaults, overrides):
    parser = configparser.RawConfigParser()

    # TODO: simply return path to config file for defaults so we can load it
    # all in the same way?
    logger.info('Loading config from builtin defaults')
    for default in defaults:
        if isinstance(default, compat.text_type):
            default = default.encode('utf-8')
        parser.readfp(io.BytesIO(default))

    # Load config from a series of config files
    files = [path.expand_path(f) for f in files]
    for name in files:
        if os.path.isdir(name):
            for filename in os.listdir(name):
                filename = os.path.join(name, filename)
                if os.path.isfile(filename) and filename.endswith('.conf'):
                    _load_file(parser, filename)
        else:
            _load_file(parser, name)

    # If there have been parse errors there is a python bug that causes the
    # values to be lists, this little trick coerces these into strings.
    parser.readfp(io.BytesIO())

    raw_config = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    logger.info('Loading config from command line options')
    for section, key, value in overrides:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


def _load_file(parser, filename):
    if not os.path.exists(filename):
        logger.debug(
            'Loading config from %s failed; it does not exist', filename)
        return
    if not os.access(filename, os.R_OK):
        logger.warning(
            'Loading config from %s failed; read permission missing',
            filename)
        return

    try:
        logger.info('Loading config from %s', filename)
        with io.open(filename, 'rb') as filehandle:
            parser.readfp(filehandle)
    except configparser.MissingSectionHeaderError as e:
        logger.warning('%s does not have a config section, not loaded.',
                       filename)
    except configparser.ParsingError as e:
        linenos = ', '.join(str(lineno) for lineno, line in e.errors)
        logger.warning(
            '%s has errors, line %s has been ignored.', filename, linenos)
    except IOError:
        # TODO: if this is the initial load of logging config we might not
        # have a logger at this point, we might want to handle this better.
        logger.debug('Config file %s not found; skipping', filename)


def _validate(raw_config, schemas):
    # Get validated config
    config = {}
    errors = {}
    sections = set(raw_config)
    for schema in schemas:
        sections.discard(schema.name)
        values = raw_config.get(schema.name, {})
        result, error = schema.deserialize(values)
        if error:
            errors[schema.name] = error
        if result:
            config[schema.name] = result

    for section in sections:
        logger.debug('Ignoring unknown config section: %s', section)

    return config, errors


def _format(config, comments, schemas, display, disable):
    output = []
    for schema in schemas:
        serialized = schema.serialize(
            config.get(schema.name, {}), display=display)
        if not serialized:
            continue
        output.append(b'[%s]' % bytes(schema.name))
        for key, value in serialized.items():
            if isinstance(value, types.DeprecatedValue):
                continue
            comment = bytes(comments.get(schema.name, {}).get(key, ''))
            output.append(b'%s =' % bytes(key))
            if value is not None:
                output[-1] += b' ' + value
            if comment:
                output[-1] += b'  ; ' + comment.capitalize()
            if disable:
                output[-1] = re.sub(r'^', b'#', output[-1], flags=re.M)
        output.append(b'')
    return b'\n'.join(output).strip()


def _preprocess(config_string):
    """Convert a raw config into a form that preserves comments etc."""
    results = ['[__COMMENTS__]']
    counter = itertools.count(0)

    section_re = re.compile(r'^(\[[^\]]+\])\s*(.+)$')
    blank_line_re = re.compile(r'^\s*$')
    comment_re = re.compile(r'^(#|;)')
    inline_comment_re = re.compile(r' ;')

    def newlines(match):
        return '__BLANK%d__ =' % next(counter)

    def comments(match):
        if match.group(1) == '#':
            return '__HASH%d__ =' % next(counter)
        elif match.group(1) == ';':
            return '__SEMICOLON%d__ =' % next(counter)

    def inlinecomments(match):
        return '\n__INLINE%d__ =' % next(counter)

    def sections(match):
        return '%s\n__SECTION%d__ = %s' % (
            match.group(1), next(counter), match.group(2))

    for line in config_string.splitlines():
        line = blank_line_re.sub(newlines, line)
        line = section_re.sub(sections, line)
        line = comment_re.sub(comments, line)
        line = inline_comment_re.sub(inlinecomments, line)
        results.append(line)
    return '\n'.join(results)


def _postprocess(config_string):
    """Converts a preprocessed config back to original form."""
    flags = re.IGNORECASE | re.MULTILINE
    result = re.sub(r'^\[__COMMENTS__\](\n|$)', '', config_string, flags=flags)
    result = re.sub(r'\n__INLINE\d+__ =(.*)$', ' ;\g<1>', result, flags=flags)
    result = re.sub(r'^__HASH\d+__ =(.*)$', '#\g<1>', result, flags=flags)
    result = re.sub(r'^__SEMICOLON\d+__ =(.*)$', ';\g<1>', result, flags=flags)
    result = re.sub(r'\n__SECTION\d+__ =(.*)$', '\g<1>', result, flags=flags)
    result = re.sub(r'^__BLANK\d+__ =$', '', result, flags=flags)
    return result


class Proxy(collections.Mapping):

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        item = self._data.__getitem__(key)
        if isinstance(item, dict):
            return Proxy(item)
        return item

    def __iter__(self):
        return self._data.__iter__()

    def __len__(self):
        return self._data.__len__()

    def __repr__(self):
        return b'Proxy(%r)' % self._data
