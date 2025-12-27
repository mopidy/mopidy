from mopidy.config import (
    Boolean,
    ConfigSchema,
    Deprecated,
    Hostname,
    Integer,
    LogColor,
    LogLevel,
    MapConfigSchema,
    Path,
    Port,
    Secret,
    String,
)

_core = ConfigSchema("core")
_core["cache_dir"] = Path()
_core["config_dir"] = Path()
_core["data_dir"] = Path()
# MPD supports at most 10k tracks, some clients segfault when this is exceeded.
_core["max_tracklist_length"] = Integer(minimum=1)
_core["restore_state"] = Boolean(optional=True)

_logging = ConfigSchema("logging")
_logging["verbosity"] = Integer(minimum=-1, maximum=4)
_logging["format"] = String()
_logging["color"] = Boolean()
_logging["console_format"] = Deprecated()
_logging["debug_format"] = Deprecated()
_logging["debug_file"] = Deprecated()
_logging["config_file"] = Path(optional=True)

_loglevels = MapConfigSchema("loglevels", LogLevel())
_logcolors_schema = MapConfigSchema("logcolors", LogColor())

_audio = ConfigSchema("audio")
_audio["mixer"] = String()
_audio["mixer_track"] = Deprecated()
_audio["mixer_volume"] = Integer(optional=True, minimum=0, maximum=100)
_audio["output"] = String()
_audio["visualizer"] = Deprecated()
_audio["buffer_time"] = Integer(optional=True, minimum=1)

_proxy = ConfigSchema("proxy")
_proxy["scheme"] = String(
    optional=True,
    choices=("http", "https", "socks4", "socks5"),
)
_proxy["hostname"] = Hostname(optional=True)
_proxy["port"] = Port(optional=True)
_proxy["username"] = String(optional=True)
_proxy["password"] = Secret(optional=True)

type ConfigSchemas = list[ConfigSchema | MapConfigSchema]
schemas: ConfigSchemas = [
    _core,
    _logging,
    _loglevels,
    _logcolors_schema,
    _audio,
    _proxy,
]
