from __future__ import unicode_literals

import os

from mopidy.utils import config


default_config_file = os.path.join(os.path.dirname(__file__), 'default.conf')
default_config = open(default_config_file).read()


config_schemas = {}  # TODO: use ordered dict?
config_schemas['logging'] = config.ConfigSchema()
config_schemas['logging']['console_format'] = config.String()
config_schemas['logging']['debug_format'] = config.String()
config_schemas['logging']['debug_file'] = config.Path()

config_schemas['logging.levels'] = config.LogLevelConfigSchema()

config_schemas['audio'] = config.ConfigSchema()
config_schemas['audio']['mixer'] = config.String()
config_schemas['audio']['mixer_track'] = config.String(optional=True)
config_schemas['audio']['output'] = config.String()

config_schemas['proxy'] = config.ConfigSchema()
config_schemas['proxy']['hostname'] = config.Hostname(optional=True)
config_schemas['proxy']['username'] = config.String(optional=True)
config_schemas['proxy']['password'] = config.String(optional=True, secret=True)

# NOTE: if multiple outputs ever comes something like LogLevelConfigSchema
#config_schemas['audio.outputs'] = config.AudioOutputConfigSchema()


def register_schema(name, schema):
    if name in config_schemas:
        raise Exception
    config_schemas[name] = schema
