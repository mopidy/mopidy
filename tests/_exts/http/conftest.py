"""Fixtures for testing Tornado applications with plain pytest.

This does the same as tornado.testing.AsyncHTTPTestCase, without unittest.
"""

import asyncio
from collections.abc import Awaitable, Callable, Iterator
from typing import Any

import pytest
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.testing
import tornado.web


class TornadoServer:
    """A Tornado application served on an unused port, with its own IOLoop."""

    def __init__(self, app: tornado.web.Application) -> None:
        self.io_loop = tornado.ioloop.IOLoop(make_current=False)
        asyncio.set_event_loop(self.io_loop.asyncio_loop)
        sock, self.port = tornado.testing.bind_unused_port()
        self.http_client = tornado.httpclient.AsyncHTTPClient()
        self.http_server = tornado.httpserver.HTTPServer(app)
        self.http_server.add_sockets([sock])

    def get_url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def run_sync(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Run a coroutine on the server's IOLoop and return its result."""
        return self.io_loop.run_sync(
            func,
            timeout=tornado.testing.get_async_test_timeout(),
        )

    def fetch(
        self,
        path: str,
        *,
        raise_error: bool = False,
        **kwargs: Any,
    ) -> tornado.httpclient.HTTPResponse:
        """Fetch a path from the server and return the response."""
        return self.run_sync(
            lambda: self.http_client.fetch(
                self.get_url(path),
                raise_error=raise_error,
                **kwargs,
            ),
        )

    def close(self) -> None:
        self.http_server.stop()
        self.run_sync(self.http_server.close_all_connections)
        self.http_client.close()
        # Cancel tasks that are still pending, so they do not warn later.
        tasks = [
            task
            for task in asyncio.all_tasks(self.io_loop.asyncio_loop)
            if not task.done()
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            self.run_sync(lambda: asyncio.wait(tasks))
        asyncio.set_event_loop(None)
        self.io_loop.close(all_fds=True)


@pytest.fixture
def tornado_server() -> Iterator[Callable[[tornado.web.Application], TornadoServer]]:
    """Factory that serves a Tornado application for the duration of a test."""
    servers: list[TornadoServer] = []

    def start(app: tornado.web.Application) -> TornadoServer:
        server = TornadoServer(app)
        servers.append(server)
        return server

    yield start

    for server in reversed(servers):
        server.close()
