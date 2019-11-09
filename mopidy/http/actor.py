import json
import logging
import threading

import pykka
import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.web
import tornado.websocket

from mopidy import exceptions, models, zeroconf
from mopidy.core import CoreListener
from mopidy.http import handlers
from mopidy.internal import encoding, formatting, network

try:
    import asyncio
except ImportError:
    asyncio = None


logger = logging.getLogger(__name__)


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    apps = []
    statics = []

    def __init__(self, config, core):
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
            error = encoding.locale_decode(exc)
            raise exceptions.FrontendError(
                f"HTTP server startup failed: {error}"
            )

        self.zeroconf_name = config["http"]["zeroconf"]
        self.zeroconf_http = None
        self.zeroconf_mopidy_http = None

    def on_start(self):
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

    def on_stop(self):
        if self.zeroconf_http:
            self.zeroconf_http.unpublish()
        if self.zeroconf_mopidy_http:
            self.zeroconf_mopidy_http.unpublish()

        self.server.stop()

    def on_event(self, name, **data):
        on_event(name, self.server.io_loop, **data)


def on_event(name, io_loop, **data):
    event = data
    event["event"] = name
    message = json.dumps(event, cls=models.ModelJSONEncoder)
    handlers.WebSocketHandler.broadcast(message, io_loop)


class HttpServer(threading.Thread):
    name = "HttpServer"

    def __init__(self, config, core, sockets, apps, statics):
        super().__init__()

        self.config = config
        self.core = core
        self.sockets = sockets
        self.apps = apps
        self.statics = statics

        self.app = None
        self.server = None
        self.io_loop = None

    def run(self):
        if asyncio:
            # If asyncio is available, Tornado uses it as its IO loop. Since we
            # start Tornado in a another thread than the main thread, we must
            # explicitly create an asyncio loop for the current thread.
            asyncio.set_event_loop(asyncio.new_event_loop())

        self.app = tornado.web.Application(self._get_request_handlers())
        self.server = tornado.httpserver.HTTPServer(self.app)
        self.server.add_sockets(self.sockets)

        self.io_loop = tornado.ioloop.IOLoop.current()
        self.io_loop.start()

        logger.debug("Stopped HTTP server")

    def stop(self):
        logger.debug("Stopping HTTP server")
        self.io_loop.add_callback(self.io_loop.stop)

    def _get_request_handlers(self):
        request_handlers = []
        request_handlers.extend(self._get_app_request_handlers())
        request_handlers.extend(self._get_static_request_handlers())
        request_handlers.extend(self._get_mopidy_request_handlers())

        logger.debug(
            "HTTP routes from extensions: %s",
            formatting.indent(
                "\n".join(
                    f"{path!r}: {handler!r}"
                    for (path, handler, *_) in request_handlers
                )
            ),
        )

        return request_handlers

    def _get_app_request_handlers(self):
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

    def _get_static_request_handlers(self):
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

    def _get_mopidy_request_handlers(self):
        return [
            (
                "/",
                tornado.web.RedirectHandler,
                {"url": "/mopidy/", "permanent": False},
            )
        ]
