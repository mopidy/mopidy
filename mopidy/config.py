from mopidy.utils import config

schemas = {}  # TODO: use ordered dict?
schemas['logging'] = config.ConfigSchema()
schemas['logging']['config_file'] = config.String()
schemas['logging']['console_format'] = config.String()
schemas['logging']['debug_format'] = config.String()
schemas['logging']['debug_file'] = config.String()
schemas['logging']['debug_thread'] = config.Boolean()

schemas['logging.levels'] = config.LogLevelConfigSchema()

schemas['audio'] = config.ConfigSchema()
schemas['audio']['mixer'] = config.String()
schemas['audio']['mixer_track'] = config.String()
schemas['audio']['output'] = config.String()

# NOTE: if multiple outputs ever comes something like LogLevelConfigSchema
#schemas['audio.outputs'] = config.AudioOutputConfigSchema()


def register_schema(name, schema):
    if name in schemas:
        raise Exception
    schemas[name] = schema
