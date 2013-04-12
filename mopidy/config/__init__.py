from __future__ import unicode_literals

import codecs
import ConfigParser as configparser
import io
import logging
import sys

from mopidy.config.schemas import *
from mopidy.config.types import *
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


def load(files, overrides, extensions=None):
    defaults = [default_config]
    if extensions:
        defaults.extend(e.get_default_config() for e in extensions)
    return _load(files, defaults, overrides)


# TODO: replace load() with this version of API.
def _load(files, defaults, overrides):
    parser = configparser.RawConfigParser()

    files = [path.expand_path(f) for f in files]
    sources = ['builtin-defaults'] + files + ['command-line']
    logger.info('Loading config from: %s', ', '.join(sources))

    for default in defaults: # TODO: remove decoding
        parser.readfp(io.StringIO(default.decode('utf-8')))

    # Load config from a series of config files
    for filename in files:
        # TODO: if this is the initial load of logging config we might not have
        # a logger at this point, we might want to handle this better.
        try:
            with codecs.open(filename, encoding='utf-8') as filehandle:
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

    for section, key, value in overrides or []:
        raw_config.setdefault(section, {})[key] = value

    return raw_config


def validate(raw_config, schemas, extensions=None):
    # Collect config schemas to validate against
    sections_and_schemas = schemas.items()
    for extension in extensions or []:
        sections_and_schemas.append(
            (extension.ext_name, extension.get_config_schema()))

    config, errors = _validate(raw_config, sections_and_schemas)

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
    for name, schema in schemas:
        try:
            items = raw_config[name].items()
            config[name] = schema.convert(items)
        except KeyError:
            errors.append('%s: section not found.' % name)
        except exceptions.ConfigError as error:
            for key in error:
                errors.append('%s/%s: %s' % (name, key, error[key]))
    # TODO: raise errors instead of return
    return config, errors


def parse_override(override):
    """Parse section/key=value override."""
    section, remainder = override.split('/', 1)
    key, value = remainder.split('=', 1)
    return (section.strip(), key.strip(), value.strip())
