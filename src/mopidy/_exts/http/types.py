from __future__ import annotations

from collections.abc import Callable
from os import PathLike
from typing import TYPE_CHECKING, Any, TypedDict

import tornado.web

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.core import CoreProxy


type RequestRule = tuple[str, type[tornado.web.RequestHandler], dict[str, Any]]


class HttpConfig(TypedDict):
    hostname: str
    port: int
    zeroconf: str | None
    allowed_origins: list[str]
    csrf_protection: bool | None
    default_app: str | None


class HttpApp(TypedDict):
    name: str
    factory: Callable[[Config, CoreProxy], list[RequestRule]]


class HttpStatic(TypedDict):
    name: str
    path: str | PathLike[str]
