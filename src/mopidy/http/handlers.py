from __future__ import annotations

import functools
import logging
import urllib.parse
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket

import mopidy
from mopidy import core
from mopidy.http.types import HttpConfig
from mopidy.internal import jsonrpc

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from typing import ClassVar

    from mopidy.core.actor import CoreProxy
    from mopidy.ext import Config
    from mopidy.http.types import HttpApp, HttpStatic, RequestRule


logger = logging.getLogger(__name__)


def make_mopidy_app_factory(
    *,
    apps: list[HttpApp],
    statics: list[HttpStatic],
) -> Callable[[Config, CoreProxy], list[RequestRule]]:
    def mopidy_app_factory(config: Config, core: CoreProxy) -> list[RequestRule]:
        http_config = cast(HttpConfig, config["http"])
        if not http_config["csrf_protection"]:
            logger.warning("HTTP Cross-Site Request Forgery protection is disabled")

        return [
            (
                r"/ws/?",
                WebSocketHandler,
                {
                    "core": core,
                    "allowed_origins": http_config["allowed_origins"],
                    "csrf_protection": http_config["csrf_protection"],
                },
            ),
            (
                r"/rpc",
                JsonRpcHandler,
                {
                    "core": core,
                    "allowed_origins": http_config["allowed_origins"],
                    "csrf_protection": http_config["csrf_protection"],
                },
            ),
            (
                r"/(.+)",
                StaticFileHandler,
                {
                    "path": str(Path(__file__).parent / "data"),
                },
            ),
            (
                r"/",
                ClientListHandler,
                {
                    "apps": apps,
                    "statics": statics,
                },
            ),
        ]

    return mopidy_app_factory


def make_jsonrpc_wrapper(core_actor: CoreProxy) -> jsonrpc.Wrapper:
    inspector = jsonrpc.Inspector(
        objects={
            "core.get_uri_schemes": core.Core.get_uri_schemes,
            "core.get_version": core.Core.get_version,
            "core.history": core.HistoryController,
            "core.library": core.LibraryController,
            "core.mixer": core.MixerController,
            "core.playback": core.PlaybackController,
            "core.playlists": core.PlaylistsController,
            "core.tracklist": core.TracklistController,
        }
    )
    return jsonrpc.Wrapper(
        objects={
            "core.describe": inspector.describe,
            "core.get_uri_schemes": core_actor.get_uri_schemes,
            "core.get_version": core_actor.get_version,
            "core.history": core_actor.history,
            "core.library": core_actor.library,
            "core.mixer": core_actor.mixer,
            "core.playback": core_actor.playback,
            "core.playlists": core_actor.playlists,
            "core.tracklist": core_actor.tracklist,
        },
    )


def _send_broadcast(
    client: WebSocketHandler,
    msg: bytes | str | dict[str, Any],
) -> None:
    # We could check for client.ws_connection, but we don't really
    # care why the broadcast failed, we just want the rest of them
    # to succeed, so catch everything.
    try:
        client.write_message(msg)
    except Exception as exc:
        logger.debug(
            f"Broadcast of WebSocket message to "
            f"{client.request.remote_ip} failed: {exc}"
        )
        # TODO: should this do the same cleanup as the on_message code?


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    # XXX This set is shared by all WebSocketHandler objects. This isn't
    # optimal, but there's currently no use case for having more than one of
    # these anyway.
    clients: ClassVar[set[WebSocketHandler]] = set()

    @classmethod
    def broadcast(
        cls,
        msg: bytes | str | dict[str, Any],
        io_loop: tornado.ioloop.IOLoop,
    ) -> None:
        # This can be called from outside the Tornado ioloop, so we need to
        # safely cross the thread boundary by adding a callback to the loop.
        for client in cls.clients.copy():
            # One callback per client to keep time we hold up the loop short
            io_loop.add_callback(functools.partial(_send_broadcast, client, msg))

    def initialize(
        self,
        core: CoreProxy,
        allowed_origins: set[str],
        csrf_protection: bool | None,
    ) -> None:
        self.jsonrpc = make_jsonrpc_wrapper(core)
        self.allowed_origins = allowed_origins
        self.csrf_protection = csrf_protection

    def open(self, *_args: str, **_kwargs: str) -> Awaitable[None] | None:
        self.set_nodelay(True)
        self.clients.add(self)
        logger.debug("New WebSocket connection from %s", self.request.remote_ip)

    def on_close(self) -> None:
        self.clients.discard(self)
        logger.debug("Closed WebSocket connection from %s", self.request.remote_ip)

    def on_message(self, message: str | bytes) -> Awaitable[None] | None:
        if not message:
            return

        logger.debug(
            "Received WebSocket message from %s: %r",
            self.request.remote_ip,
            message,
        )

        try:
            response = self.jsonrpc.handle_json(tornado.escape.native_str(message))
            if response and self.write_message(response):
                logger.debug(
                    "Sent WebSocket message to %s: %r",
                    self.request.remote_ip,
                    response,
                )
        except Exception as exc:
            logger.error(f"WebSocket request error: {exc}")
            self.close()

    def check_origin(self, origin: str) -> bool:
        if not self.csrf_protection:
            return True
        return check_origin(origin, self.request.headers, self.allowed_origins)


def set_mopidy_headers(request_handler: tornado.web.RequestHandler) -> None:
    request_handler.set_header("Cache-Control", "no-cache")
    request_handler.set_header("X-Mopidy-Version", mopidy.__version__.encode())


def check_origin(
    origin: str | None,
    request_headers: tornado.httputil.HTTPHeaders,
    allowed_origins: set[str],
) -> bool:
    if origin is None:
        logger.warning("HTTP request denied for missing Origin header")
        return False
    host_header = request_headers.get("Host")
    parsed_origin = urllib.parse.urlparse(origin).netloc.lower()
    # Some frameworks (e.g. Apache Cordova) use local files. Requests from
    # these files don't really have a sensible Origin so the browser sets the
    # header to something like 'file://' or 'null'. This results here in an
    # empty parsed_origin which we choose to allow.
    if parsed_origin and parsed_origin not in allowed_origins | {host_header}:
        logger.warning('HTTP request denied for Origin "%s"', origin)
        return False
    return True


class JsonRpcHandler(tornado.web.RequestHandler):
    def initialize(
        self,
        core: CoreProxy,
        allowed_origins: set[str],
        csrf_protection: bool | None,
    ) -> None:
        self.jsonrpc = make_jsonrpc_wrapper(core)
        self.allowed_origins = allowed_origins
        self.csrf_protection = csrf_protection

    def head(self) -> Awaitable[None] | None:
        self.set_extra_headers()
        self.finish()

    def post(self) -> Awaitable[None] | None:
        if self.csrf_protection:
            # This "non-standard" Content-Type requirement forces browsers to
            # automatically issue a preflight OPTIONS request before this one.
            # All Origin header enforcement/checking can be limited to our OPTIONS
            # handler and requests not vulnerable to CSRF (i.e. non-browser
            # requests) need only set the Content-Type header.
            content_type = (
                self.request.headers.get("Content-Type", "").split(";")[0].strip()
            )
            if content_type != "application/json":
                self.set_status(415, "Content-Type must be application/json")
                return

            origin = self.request.headers.get("Origin")
            if origin is not None:
                # This request came from a browser and has already had its Origin
                # checked in the preflight request.
                self.set_cors_headers(origin)

        data = self.request.body
        if not data:
            return

        logger.debug("Received RPC message from %s: %r", self.request.remote_ip, data)

        try:
            self.set_extra_headers()
            response = self.jsonrpc.handle_json(tornado.escape.native_str(data))
            if response and self.write(response):
                logger.debug(
                    "Sent RPC message to %s: %r",
                    self.request.remote_ip,
                    response,
                )
        except Exception as e:
            logger.error("HTTP JSON-RPC request error: %s", e)
            self.write_error(500)

    def set_extra_headers(self) -> None:
        set_mopidy_headers(self)
        self.set_header("Accept", "application/json")
        self.set_header("Content-Type", "application/json; utf-8")

    def set_cors_headers(self, origin: str) -> None:
        self.set_header("Access-Control-Allow-Origin", f"{origin}")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self) -> Awaitable[None] | None:
        if self.csrf_protection:
            origin = cast(str | None, self.request.headers.get("Origin"))
            if not check_origin(origin, self.request.headers, self.allowed_origins):
                self.set_status(403, f"Access denied for origin {origin}")
                return

            assert origin
            self.set_cors_headers(origin)

        self.set_status(204)
        self.finish()


class ClientListHandler(tornado.web.RequestHandler):
    def initialize(self, apps: list[HttpApp], statics: list[HttpStatic]) -> None:
        self.apps = apps
        self.statics = statics

    def get_template_path(self) -> str:
        return str(Path(__file__).parent)

    def get(self) -> Awaitable[None] | None:
        set_mopidy_headers(self)

        names = set()
        for app in self.apps:
            names.add(app["name"])
        for static in self.statics:
            names.add(static["name"])
        names.discard("mopidy")

        self.render("data/clients.html", apps=sorted(names))


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(
        self,
        path: str,  # noqa: ARG002
    ) -> None:
        set_mopidy_headers(self)


class AddSlashHandler(tornado.web.RequestHandler):
    @tornado.web.addslash
    def prepare(self) -> Awaitable[None] | None:
        return super().prepare()
