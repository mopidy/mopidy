from __future__ import unicode_literals

from mopidy.config.schemas import *
from mopidy.config.values import *


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
