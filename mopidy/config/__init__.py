from __future__ import unicode_literals

import codecs
import ConfigParser as configparser
import io
import logging
import sys

from mopidy.config.schemas import *
from mopidy.config.values import *
from mopidy.utils import path

logger = logging.getLogger('mopdiy.config')


default_config = """
[logging]
console_format = %(levelname)-8s %(message)s
debug_format = %(levelname)-8s %(asctime)s [%(process)d:%(threadName)s] %(name)s\n  %(message)s
debug_file = mopidy.log

[logging.levels]
pykka = info

[audio]
mixer = autoaudiomixer
mixer_track =
output = autoaudiosink

[proxy]
hostname =
username =
password =
"""

config_schemas = {}  # TODO: use ordered dict?
config_schemas['logging'] = ConfigSchema()
config_schemas['logging']['console_format'] = String()
config_schemas['logging']['debug_format'] = String()
config_schemas['logging']['debug_file'] = Path()

config_schemas['logging.levels'] = LogLevelConfigSchema()

config_schemas['audio'] = ConfigSchema()
config_schemas['audio']['mixer'] = String()
config_schemas['audio']['mixer_track'] = String(optional=True)
config_schemas['audio']['output'] = String()

config_schemas['proxy'] = ConfigSchema()
config_schemas['proxy']['hostname'] = Hostname(optional=True)
config_schemas['proxy']['username'] = String(optional=True)
config_schemas['proxy']['password'] = String(optional=True, secret=True)

# NOTE: if multiple outputs ever comes something like LogLevelConfigSchema
#config_schemas['audio.outputs'] = config.AudioOutputConfigSchema()


# TODO: update API to load(files, defaults, overrides) this should not need to
# know about extensions
def load(files, overrides, extensions=None):
    parser = configparser.RawConfigParser()

    files = [path.expand_path(f) for f in files]
    sources = ['builtin-defaults'] + files + ['command-line']
    logger.info('Loading config from: %s', ', '.join(sources))

    # Read default core config
    parser.readfp(io.StringIO(default_config))

    # Read default extension config
    for extension in extensions or []:
        parser.readfp(io.StringIO(extension.get_default_config()))

    # Load config from a series of config files
    for filename in files:
        # TODO: if this is the initial load of logging config we might not have
        # a logger at this point, we might want to handle this better.
        try:
            filehandle = codecs.open(filename, encoding='utf-8')
            parser.readfp(filehandle)
        except IOError:
            logger.debug('Config file %s not found; skipping', filename)
            continue
        except UnicodeDecodeError:
            logger.error('Config file %s is not UTF-8 encoded', filename)
            sys.exit(1)

    raw_config = {}
    for section in parser.sections():
        raw_config[section] = dict(parser.items(section))

    # TODO: move out of file loading code?
    for section, key, value in overrides or []:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


# TODO: switch API to validate(raw_config, schemas) this should not need to
# know about extensions
def validate(raw_config, schemas, extensions=None):
    # Collect config schemas to validate against
    sections_and_schemas = schemas.items()
    for extension in extensions or []:
        sections_and_schemas.append(
            (extension.ext_name, extension.get_config_schema()))

    # Get validated config
    config = {}
    errors = {}
    for section_name, schema in sections_and_schemas:
        if section_name not in raw_config:
            errors[section_name] = {section_name: 'section not found'}
        try:
            items = raw_config[section_name].items()
            config[section_name] = schema.convert(items)
        except exceptions.ConfigError as error:
            errors[section_name] = error

    if errors:
        # TODO: raise error instead.
        #raise exceptions.ConfigError(errors)
        for section_name, error in errors.items():
            logger.error('[%s] config errors:', section_name)
            for key in error:
                logger.error('%s %s', key, error[key])
        sys.exit(1)

    return config


def parse_override(override):
    """Parse section/key=value override."""
    section, remainder = override.split('/', 1)
    key, value = remainder.split('=', 1)
    return (section, key, value)
