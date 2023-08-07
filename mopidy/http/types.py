from __future__ import annotations

from os import PathLike
from typing import TYPE_CHECKING, Any, Callable, Optional, TypedDict

import tornado.web

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from mopidy.core.actor import CoreProxy
    from mopidy.ext import Config


RequestRule: TypeAlias = tuple[str, type[tornado.web.RequestHandler], dict[str, Any]]


class HttpConfig(TypedDict):
    hostname: str
    port: int
    zeroconf: Optional[str]
    allowed_origins: list[str]
    csrf_protection: Optional[bool]
    default_app: Optional[str]


class HttpApp(TypedDict):
    name: str
    factory: Callable[[Config, CoreProxy], list[RequestRule]]


class HttpStatic(TypedDict):
    name: str
    path: str | PathLike[str]
