from __future__ import annotations

import pathlib
from typing import Any, Literal, TypedDict

LogColorName = Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]
LogLevelName = Literal[
    "critical",
    "error",
    "warning",
    "info",
    "debug",
    "trace",
    "all",
]

type ConfigDict = dict[str, dict[str, Any]]


class Config(TypedDict):
    core: CoreConfig
    logging: LoggingConfig
    loglevels: dict[LogLevelName, int]
    logcolors: dict[LogLevelName, LogColorName]
    audio: AudioConfig
    proxy: ProxyConfig


class CoreConfig(TypedDict):
    cache_dir: pathlib.Path
    config_dir: pathlib.Path
    data_dir: pathlib.Path
    max_tracklist_length: int
    restore_state: bool


class LoggingConfig(TypedDict):
    verbosity: int
    format: str
    color: bool
    config_file: pathlib.Path | None


class AudioConfig(TypedDict):
    mixer: str
    mixer_volume: int | None
    output: str
    buffer_time: int | None


class ProxyConfig(TypedDict):
    scheme: str | None
    hostname: str | None
    port: int | None
    username: str | None
    password: str | None
