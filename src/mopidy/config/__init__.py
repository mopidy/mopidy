from __future__ import annotations

import pathlib

from mopidy.config._types import (
    AudioConfig,
    Config,
    CoreConfig,
    LoggingConfig,
    ProxyConfig,
)
from mopidy.config.schemas import ConfigSchema, MapConfigSchema
from mopidy.config.types import (
    Boolean,
    ConfigValue,
    Deprecated,
    DeprecatedValue,
    Float,
    Hostname,
    Integer,
    List,
    LogColor,
    LogLevel,
    Pair,
    Path,
    Port,
    Secret,
    String,
)

__all__ = [
    "AudioConfig",
    "Boolean",
    "Config",
    "ConfigSchema",
    "ConfigValue",
    "CoreConfig",
    "Deprecated",
    "DeprecatedValue",
    "Float",
    "Hostname",
    "Integer",
    "List",
    "LogColor",
    "LogLevel",
    "LoggingConfig",
    "MapConfigSchema",
    "Pair",
    "Path",
    "Port",
    "ProxyConfig",
    "Secret",
    "String",
    "read",
]


def read(config_file: pathlib.Path) -> str:
    """Helper to load config defaults in same way across core and extensions."""
    return pathlib.Path(config_file).read_text(errors="surrogateescape")
