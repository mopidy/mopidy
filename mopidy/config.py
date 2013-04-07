from __future__ import unicode_literals

from mopidy.utils import config


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
