from __future__ import annotations

import pathlib
from collections.abc import Iterator, Mapping
from contextvars import ContextVar
from typing import Any, ClassVar, Literal, TypedDict, overload, override

LogLevelName = Literal[
    "critical",
    "error",
    "warning",
    "info",
    "debug",
    "trace",
    "all",
]


class Config(Mapping):
    _instance: ClassVar[ContextVar[Config | None]] = ContextVar("Config", default=None)

    @classmethod
    def get_global(cls) -> Config:
        if (instance := cls._instance.get()) is None:
            msg = f"{cls} not set in context"
            raise RuntimeError(msg)
        return instance

    @classmethod
    def set_global(cls, instance: Config) -> None:
        if cls._instance.get() is not None:
            msg = f"{cls} already set in context"
            raise RuntimeError(msg)
        cls._instance.set(instance)

    def __init__(self, data: dict[str, dict[str, Any]]) -> None:
        self._data = data

    @overload
    def __getitem__(self, key: Literal["core"]) -> CoreConfig: ...  # pyright: ignore[reportOverlappingOverload]
    @overload
    def __getitem__(self, key: Literal["logging"]) -> LoggingConfig: ...
    @overload
    def __getitem__(self, key: Literal["loglevels"]) -> dict[LogLevelName, int]: ...
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
        | AudioConfig
        | ProxyConfig
    ):
        return ConfigSection(key, self._data.__getitem__(key))

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
