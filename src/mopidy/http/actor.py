from __future__ import annotations

import asyncio
import logging
import secrets
import socket
import threading
from typing import TYPE_CHECKING, Any, ClassVar

import msgspec
import pykka
import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.web
import tornado.websocket

from mopidy import exceptions, zeroconf
from mopidy.core import CoreListener
from mopidy.http import Extension, handlers
from mopidy.internal import formatting, network

if TYPE_CHECKING:
    from mopidy.core.actor import CoreProxy
    from mopidy.ext import Config
    from mopidy.http.types import HttpApp, HttpStatic, RequestRule


logger = logging.getLogger(__name__)


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    apps: ClassVar[list[HttpApp]] = []
    statics: ClassVar[list[HttpStatic]] = []

    def __init__(self, config: Config, core: CoreProxy) -> None:
        super().__init__()

        self.hostname = network.format_hostname(config["http"]["hostname"])
        self.port = config["http"]["port"]
        tornado_hostname = config["http"]["hostname"]
        if tornado_hostname == "::":
            tornado_hostname = None

        try:
            logger.debug("Starting HTTP server")
            sockets = tornado.netutil.bind_sockets(self.port, tornado_hostname)
            self.server = HttpServer(
                config=config,
                core=core,
                sockets=sockets,
                apps=self.apps,
                statics=self.statics,
            )
        except OSError as exc:
            raise exceptions.FrontendError("HTTP server startup failed.") from exc

        self.zeroconf_name = config["http"]["zeroconf"]
        self.zeroconf_http = None
        self.zeroconf_mopidy_http = None

    def on_start(self) -> None:
        logger.info("HTTP server running at [%s]:%s", self.hostname, self.port)
        self.server.start()

        if self.zeroconf_name:
            self.zeroconf_http = zeroconf.Zeroconf(
                name=self.zeroconf_name, stype="_http._tcp", port=self.port
            )
            self.zeroconf_mopidy_http = zeroconf.Zeroconf(
                name=self.zeroconf_name,
                stype="_mopidy-http._tcp",
                port=self.port,
            )
            self.zeroconf_http.publish()
            self.zeroconf_mopidy_http.publish()

    def on_stop(self) -> None:
        if self.zeroconf_http:
            self.zeroconf_http.unpublish()
        if self.zeroconf_mopidy_http:
            self.zeroconf_mopidy_http.unpublish()

        self.server.stop()

    def on_event(self, event: str, **data: Any) -> None:
        assert self.server.io_loop
        on_event(event, self.server.io_loop, **data)


def on_event(name: str, io_loop: tornado.ioloop.IOLoop, **data: Any) -> None:
    event = data
    event["event"] = name
    message = msgspec.json.encode(event)
    handlers.WebSocketHandler.broadcast(message, io_loop)


class HttpServer(threading.Thread):
    name = "HttpServer"

    def __init__(  # noqa: PLR0913
        self,
        config: Config,
        core: CoreProxy,
        sockets: list[socket.socket],
        apps: list[HttpApp],
        statics: list[HttpStatic],
    ) -> None:
        super().__init__()

        self.config = config
        self.core = core
        self.sockets = sockets
        self.apps = apps
        self.statics = statics

        self.app = None
        self.server = None
        self.io_loop = None

    def run(self) -> None:
        # Since we start Tornado in a another thread than the main thread,
        # we must explicitly create an asyncio loop for the current thread.
        asyncio.set_event_loop(asyncio.new_event_loop())

        self.app = tornado.web.Application(
            self._get_request_handlers(),  # pyright: ignore[reportArgumentType]
            cookie_secret=self._get_cookie_secret(),
        )
        self.server = tornado.httpserver.HTTPServer(self.app)
        self.server.add_sockets(self.sockets)

        self.io_loop = tornado.ioloop.IOLoop.current()
        self.io_loop.start()

        logger.debug("Stopped HTTP server")

    def stop(self) -> None:
        logger.debug("Stopping HTTP server")
        assert self.io_loop
        self.io_loop.add_callback(self.io_loop.stop)

    def _get_request_handlers(self) -> list[RequestRule]:
        request_handlers = []
        request_handlers.extend(self._get_app_request_handlers())
        request_handlers.extend(self._get_static_request_handlers())
        request_handlers.extend(self._get_default_request_handlers())

        logger.debug(
            "HTTP routes from extensions: %s",
            formatting.indent(
                "\n".join(
                    f"{path!r}: {handler!r}" for (path, handler, *_) in request_handlers
                )
            ),
        )

        return request_handlers

    def _get_app_request_handlers(self) -> list[RequestRule]:
        result = []
        for app in self.apps:
            try:
                request_handlers = app["factory"](self.config, self.core)
            except Exception:
                logger.exception("Loading %s failed.", app["name"])
                continue

            result.append((f"/{app['name']}", handlers.AddSlashHandler))
            for handler in request_handlers:
                handler = list(handler)
                handler[0] = f"/{app['name']}{handler[0]}"
                result.append(tuple(handler))
            logger.debug("Loaded HTTP extension: %s", app["name"])
        return result

    def _get_static_request_handlers(self) -> list[RequestRule]:
        result = []
        for static in self.statics:
            result.append((f"/{static['name']}", handlers.AddSlashHandler))
            result.append(
                (
                    f"/{static['name']}/(.*)",
                    handlers.StaticFileHandler,
                    {"path": static["path"], "default_filename": "index.html"},
                )
            )
            logger.debug("Loaded static HTTP extension: %s", static["name"])
        return result

    def _get_default_request_handlers(self) -> list[RequestRule]:
        sites = [app["name"] for app in self.apps + self.statics]

        default_app = self.config["http"]["default_app"]
        if default_app not in sites:
            logger.warning(f"HTTP server's default app {default_app!r} not found")
            default_app = "mopidy"
        logger.debug(f"Default webclient is {default_app}")

        return [
            (
                r"/",
                tornado.web.RedirectHandler,
                {"url": f"/{default_app}/", "permanent": False},
            )
        ]

    def _get_cookie_secret(self) -> str:
        file_path = Extension.get_data_dir(self.config) / "cookie_secret"
        if not file_path.is_file():
            cookie_secret = secrets.token_hex(32)
            file_path.write_text(cookie_secret)
        else:
            cookie_secret = file_path.read_text().strip()
            if not cookie_secret:
                logging.error(
                    f"HTTP server could not find cookie secret in {file_path}"
                )
        return cookie_secret
