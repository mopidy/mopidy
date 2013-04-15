from __future__ import unicode_literals

import ConfigParser as configparser
import io
import logging
import os.path
import sys

from mopidy.config.schemas import *
from mopidy.config.types import *
from mopidy.utils import path

logger = logging.getLogger('mopdiy.config')

_logging_schema = ConfigSchema('logging')
_logging_schema['console_format'] = String()
_logging_schema['debug_format'] = String()
_logging_schema['debug_file'] = Path()

_loglevels_schema = LogLevelConfigSchema('logging.levels')

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

core_schemas = [_logging_schema, _loglevels_schema, _audio_schema, _proxy_schema]


def read(config_file):
    """Helper to load config defaults in same way across core and extensions"""
    with io.open(config_file, 'rb') as filehandle:
        return filehandle.read()


def load(files, overrides, extensions=None):
    config_dir = os.path.dirname(__file__)
    defaults = [read(os.path.join(config_dir, 'default.conf'))]
    if extensions:
        defaults.extend(e.get_default_config() for e in extensions)
    return _load(files, defaults, overrides)


# TODO: replace load() with this version of API.
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


def validate(raw_config, schemas, extensions=None):
    # Collect config schemas to validate against
    extension_schemas = [e.get_config_schema() for e in extensions or []]
    config, errors = _validate(raw_config, schemas + extension_schemas)

    if errors:
        # TODO: raise error instead.
        #raise exceptions.ConfigError(errors)
        for error in errors:
            logger.error(error)
        sys.exit(1)

    return config


# TODO: replace validate() with this version of API.
def _validate(raw_config, schemas):
    # Get validated config
    config = {}
    errors = []
    for schema in schemas:
        try:
            items = raw_config[schema.name].items()
            config[schema.name] = schema.convert(items)
        except KeyError:
            errors.append('%s: section not found.' % schema.name)
        except exceptions.ConfigError as error:
            for key in error:
                errors.append('%s/%s: %s' % (schema.name, key, error[key]))
    # TODO: raise errors instead of return
    return config, errors


def parse_override(override):
    """Parse ``section/key=value`` command line overrides"""
    section, remainder = override.split('/', 1)
    key, value = remainder.split('=', 1)
    return (section.strip(), key.strip(), value.strip())
