from __future__ import unicode_literals

import ConfigParser as configparser
import io
import logging
import os.path

from mopidy.config.schemas import *
from mopidy.config.types import *
from mopidy.utils import path

logger = logging.getLogger('mopidy.config')

_logging_schema = ConfigSchema('logging')
_logging_schema['console_format'] = String()
_logging_schema['debug_format'] = String()
_logging_schema['debug_file'] = Path()

_loglevels_schema = LogLevelConfigSchema('loglevels')

_audio_schema = ConfigSchema('audio')
_audio_schema['mixer'] = String()
_audio_schema['mixer_track'] = String(optional=True)
_audio_schema['output'] = String()

_proxy_schema = ConfigSchema('proxy')
_proxy_schema['hostname'] = Hostname(optional=True)
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
    raw_config = _load(files, defaults, overrides)

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
    sources = ['builtin-defaults'] + files + ['command-line']
    logger.info('Loading config from: %s', ', '.join(sources))

    # TODO: simply return path to config file for defaults so we can load it
    # all in the same way?
    for default in defaults:
        parser.readfp(io.BytesIO(default))

    # Load config from a series of config files
    for filename in files:
        try:
            with io.open(filename, 'rb') as filehandle:
                parser.readfp(filehandle)
        except IOError:
            # TODO: if this is the initial load of logging config we might not
            # have a logger at this point, we might want to handle this better.
            logger.debug('Config file %s not found; skipping', filename)

    raw_config = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    for section, key, value in overrides or []:
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
        serialized = schema.serialize(config.get(schema.name, {}), display=display)
        output.append(b'[%s]' % schema.name)
        for key, value in serialized.items():
            comment = comments.get(schema.name, {}).get(key, b'')
            output.append(b'%s =' % key)
            if value is not None:
                output[-1] += b' ' + value
            if comment:
                output[-1] += b'  # ' + comment.capitalize()
        output.append(b'')
    return b'\n'.join(output)


def parse_override(override):
    """Parse ``section/key=value`` command line overrides"""
    section, remainder = override.split('/', 1)
    key, value = remainder.split('=', 1)
    return (section.strip(), key.strip(), value.strip())
