from __future__ import annotations

import pathlib
from collections.abc import Iterator, Mapping
from typing import Any, Literal, TypedDict, overload, override

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


class Config(Mapping):
    def __init__(self, data: dict[str, dict[str, Any]]) -> None:
        self._data = data

    @overload
    def __getitem__(self, key: Literal["core"]) -> CoreConfig: ...  # pyright: ignore[reportOverlappingOverload]
    @overload
    def __getitem__(self, key: Literal["logging"]) -> LoggingConfig: ...
    @overload
    def __getitem__(self, key: Literal["loglevels"]) -> dict[LogLevelName, int]: ...
    @overload
    def __getitem__(
        self, key: Literal["logcolors"]
    ) -> dict[LogLevelName, LogColorName]: ...
    @overload
    def __getitem__(self, key: Literal["audio"]) -> AudioConfig: ...
    @overload
    def __getitem__(self, key: Literal["proxy"]) -> ProxyConfig: ...
    @overload
    def __getitem__(self, key: ...) -> ConfigSection: ...

    @override
    def __getitem__(
        self, key: str
    ) -> (
        ConfigSection
        | CoreConfig
        | LoggingConfig
        | dict[LogLevelName, int]
        | dict[LogLevelName, LogColorName]
        | AudioConfig
        | ProxyConfig
    ):
        return ConfigSection(key, self._data.__getitem__(key))

    def __setitem__(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = value

    @override
    def __iter__(self) -> Iterator[str]:
        return self._data.__iter__()

    @override
    def __len__(self) -> int:
        return self._data.__len__()

    def __repr__(self) -> str:
        return f"Config({self._data!r})"


class ConfigSection(Mapping):
    def __init__(self, name: str, data: dict[str, Any]) -> None:
        self._name = name
        self._data = data

    @override
    def __getitem__(self, key: str) -> Any:
        return self._data.__getitem__(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    @override
    def __iter__(self) -> Iterator[str]:
        return self._data.__iter__()

    @override
    def __len__(self) -> int:
        return self._data.__len__()

    def __repr__(self) -> str:
        return f"ConfigSection({self._name!r}, {self._data!r})"


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
