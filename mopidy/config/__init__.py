from __future__ import unicode_literals

import ConfigParser as configparser
import io
import itertools
import logging
import os.path
import re

from mopidy.config import keyring
from mopidy.config.schemas import *  # noqa
from mopidy.config.types import *  # noqa
from mopidy.utils import path

logger = logging.getLogger('mopidy.config')

_logging_schema = ConfigSchema('logging')
_logging_schema['console_format'] = String()
_logging_schema['debug_format'] = String()
_logging_schema['debug_file'] = Path()
_logging_schema['config_file'] = Path(optional=True)

_loglevels_schema = LogLevelConfigSchema('loglevels')

_audio_schema = ConfigSchema('audio')
_audio_schema['mixer'] = String()
_audio_schema['mixer_track'] = String(optional=True)
_audio_schema['output'] = String()
_audio_schema['visualizer'] = String(optional=True)

_proxy_schema = ConfigSchema('proxy')
_proxy_schema['scheme'] = String(optional=True,
                                 choices=['http', 'https', 'socks4', 'socks5'])
_proxy_schema['hostname'] = Hostname(optional=True)
_proxy_schema['port'] = Port(optional=True)
_proxy_schema['username'] = String(optional=True)
_proxy_schema['password'] = Secret(optional=True)

# NOTE: if multiple outputs ever comes something like LogLevelConfigSchema
#_outputs_schema = config.AudioOutputConfigSchema()

_schemas = [_logging_schema, _loglevels_schema, _audio_schema, _proxy_schema]


def read(config_file):
    """Helper to load config defaults in same way across core and extensions"""
    with io.open(config_file, 'rb') as filehandle:
        return filehandle.read()


def load(files, extensions, overrides):
    # Helper to get configs, as the rest of our config system should not need
    # to know about extensions.
    config_dir = os.path.dirname(__file__)
    defaults = [read(os.path.join(config_dir, 'default.conf'))]
    defaults.extend(e.get_default_config() for e in extensions)
    raw_config = _load(files, defaults, keyring.fetch() + (overrides or []))

    schemas = _schemas[:]
    schemas.extend(e.get_config_schema() for e in extensions)
    return _validate(raw_config, schemas)


def format(config, extensions, comments=None, display=True):
    # Helper to format configs, as the rest of our config system should not
    # need to know about extensions.
    schemas = _schemas[:]
    schemas.extend(e.get_config_schema() for e in extensions)
    return _format(config, comments or {}, schemas, display)


def _load(files, defaults, overrides):
    parser = configparser.RawConfigParser()

    files = [path.expand_path(f) for f in files]
    sources = ['builtin defaults'] + files + ['command line options']
    logger.info('Loading config from: %s', ', '.join(sources))

    # TODO: simply return path to config file for defaults so we can load it
    # all in the same way?
    for default in defaults:
        if isinstance(default, unicode):
            default = default.encode('utf-8')
        parser.readfp(io.BytesIO(default))

    # Load config from a series of config files
    for filename in files:
        try:
            with io.open(filename, 'rb') as filehandle:
                parser.readfp(filehandle)
        except configparser.MissingSectionHeaderError as e:
            logging.warning('%s does not have a config section, not loaded.',
                            filename)
        except configparser.ParsingError as e:
            linenos = ', '.join(str(lineno) for lineno, line in e.errors)
            logger.warning(
                '%s has errors, line %s has been ignored.', filename, linenos)
        except IOError:
            # TODO: if this is the initial load of logging config we might not
            # have a logger at this point, we might want to handle this better.
            logger.debug('Config file %s not found; skipping', filename)

    # If there have been parse errors there is a python bug that causes the
    # values to be lists, this little trick coerces these into strings.
    parser.readfp(io.BytesIO())

    raw_config = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    for section, key, value in overrides:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


def _validate(raw_config, schemas):
    # Get validated config
    config = {}
    errors = {}
    for schema in schemas:
        values = raw_config.get(schema.name, {})
        result, error = schema.deserialize(values)
        if error:
            errors[schema.name] = error
        if result:
            config[schema.name] = result
    return config, errors


def _format(config, comments, schemas, display):
    output = []
    for schema in schemas:
        serialized = schema.serialize(
            config.get(schema.name, {}), display=display)
        if not serialized:
            continue
        output.append(b'[%s]' % bytes(schema.name))
        for key, value in serialized.items():
            comment = bytes(comments.get(schema.name, {}).get(key, ''))
            output.append(b'%s =' % bytes(key))
            if value is not None:
                output[-1] += b' ' + value
            if comment:
                output[-1] += b'  # ' + comment.capitalize()
        output.append(b'')
    return b'\n'.join(output)


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
