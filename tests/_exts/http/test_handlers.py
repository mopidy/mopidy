from pathlib import Path
from unittest import mock

import pytest
import tornado.httpclient
import tornado.web
import tornado.websocket

from mopidy._exts.http import handlers
from mopidy._lib.version import get_version


@pytest.fixture
def static_server(tornado_server):
    app = tornado.web.Application(
        [
            (
                r"/(.*)",
                handlers.StaticFileHandler,
                {
                    "path": Path(__file__).parent,
                    "default_filename": "test_handlers.py",
                },
            ),
        ],
    )
    return tornado_server(app)


def test_static_handler(static_server):
    response = static_server.fetch("/test_handlers.py", method="GET")

    assert response.code == 200
    assert response.headers["X-Mopidy-Version"] == get_version()
    assert response.headers["Cache-Control"] == "no-cache"


def test_static_default_filename(static_server):
    response = static_server.fetch("/", method="GET")

    assert response.code == 200
    assert response.headers["X-Mopidy-Version"] == get_version()
    assert response.headers["Cache-Control"] == "no-cache"


@pytest.fixture
def ws_server(tornado_server):
    app = tornado.web.Application(
        [
            (
                r"/ws/?",
                handlers.WebSocketHandler,
                {
                    "core": mock.Mock(),
                    "allowed_origins": frozenset(),
                    "csrf_protection": True,
                },
            ),
        ],
    )
    return tornado_server(app)


def ws_connect(server, **kwargs):
    conn_kwargs = {
        "url": server.get_url("/ws").replace("http", "ws"),
    }
    conn_kwargs.update(kwargs)
    request = tornado.httpclient.HTTPRequest(**conn_kwargs)
    return tornado.websocket.websocket_connect(request)


def test_ws_invalid_json_rpc_request_doesnt_crash_handler(ws_server):
    async def run():
        # An uncaught error would result in no message, so this is just a
        # simplistic test to verify this.
        conn = await ws_connect(ws_server)
        conn.write_message("invalid request")
        message = await conn.read_message()
        assert message

    ws_server.run_sync(run)


def test_ws_broadcast_makes_it_to_client(ws_server):
    async def run():
        conn = await ws_connect(ws_server)
        handlers.WebSocketHandler.broadcast("message", ws_server.io_loop)
        message = await conn.read_message()
        assert message == "message"

    ws_server.run_sync(run)


def test_ws_broadcast_to_client_that_just_closed_connection(ws_server):
    async def run():
        conn = await ws_connect(ws_server)
        conn.stream.close()
        handlers.WebSocketHandler.broadcast("message", ws_server.io_loop)

    ws_server.run_sync(run)


def test_ws_broadcast_to_client_without_ws_connection_present(ws_server):
    async def run():
        await ws_connect(ws_server)
        # Tornado checks for ws_connection and raises WebSocketClosedError
        # if it is missing, this test case simulates winning a race were
        # this has happened but we have not yet been removed from clients.
        for client in handlers.WebSocketHandler.clients:
            client.ws_connection = None
        handlers.WebSocketHandler.broadcast("message", ws_server.io_loop)

    ws_server.run_sync(run)


def test_ws_good_origin(ws_server):
    async def run():
        headers = {"Origin": "http://localhost", "Host": "localhost"}
        conn = await ws_connect(ws_server, headers=headers)
        assert conn

    ws_server.run_sync(run)


def test_ws_bad_origin(ws_server):
    async def run():
        headers = {"Origin": "http://foobar", "Host": "localhost"}
        with pytest.raises(tornado.httpclient.HTTPClientError) as exc_info:
            _ = await ws_connect(ws_server, headers=headers)
        assert exc_info.value.code == 403

    ws_server.run_sync(run)


@pytest.fixture
def start_rpc_server(tornado_server):
    def start(*, csrf_protection):
        app = tornado.web.Application(
            [
                (
                    r"/rpc",
                    handlers.JsonRpcHandler,
                    {
                        "core": mock.Mock(),
                        "allowed_origins": set(),
                        "csrf_protection": csrf_protection,
                    },
                ),
            ],
        )
        return tornado_server(app)

    return start


@pytest.fixture
def rpc_server(start_rpc_server):
    return start_rpc_server(csrf_protection=True)


@pytest.fixture
def rpc_server_no_csrf(start_rpc_server):
    return start_rpc_server(csrf_protection=False)


@pytest.fixture
def headers():
    return {"Host": "localhost:6680"}


def assert_extra_response_headers(headers):
    assert headers["Cache-Control"] == "no-cache"
    assert headers["X-Mopidy-Version"] == get_version()
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json; utf-8"


def get_cors_response_headers(headers):
    yield (
        "Access-Control-Allow-Origin",
        headers.get("Origin"),
    )
    yield (
        "Access-Control-Allow-Headers",
        "Content-Type",
    )


def get_preflight_response_headers(headers):
    yield from get_cors_response_headers(headers)
    yield (
        "Access-Control-Max-Age",
        "7200",
    )


@pytest.mark.parametrize("csrf_protection", [True, False])
def test_rpc_head(start_rpc_server, csrf_protection):
    server = start_rpc_server(csrf_protection=csrf_protection)

    response = server.fetch("/rpc", method="HEAD")

    assert response.code == 200
    assert_extra_response_headers(response.headers)


def test_rpc_options_sets_cors_headers(rpc_server, headers):
    headers.update({"Origin": "http://localhost:6680"})
    response = rpc_server.fetch("/rpc", method="OPTIONS", headers=headers)

    assert response.code == 204
    for k, v in get_preflight_response_headers(headers):
        assert response.headers[k] == v


def test_rpc_options_bad_origin_forbidden(rpc_server, headers):
    headers.update({"Origin": "http://foo:6680"})
    response = rpc_server.fetch("/rpc", method="OPTIONS", headers=headers)

    assert response.code == 403
    assert response.reason == "Access denied for origin http://foo:6680"
    for k, _ in get_preflight_response_headers(headers):
        assert k not in response.headers


def test_rpc_options_no_origin_forbidden(rpc_server, headers):
    response = rpc_server.fetch("/rpc", method="OPTIONS", headers=headers)

    assert response.code == 403
    assert response.reason == "Access denied for origin None"
    for k, _ in get_preflight_response_headers(headers):
        assert k not in response.headers


def test_rpc_post_no_content_type_unsupported(rpc_server, headers):
    response = rpc_server.fetch("/rpc", method="POST", body="hi", headers=headers)

    assert response.code == 415
    for k, _ in get_preflight_response_headers(headers):
        assert k not in response.headers


def test_rpc_post_wrong_content_type_unsupported(rpc_server, headers):
    headers.update({"Content-Type": "application/cats"})
    response = rpc_server.fetch("/rpc", method="POST", body="hi", headers=headers)

    assert response.code == 415
    assert response.reason == "Content-Type must be application/json"
    for k, _ in get_preflight_response_headers(headers):
        assert k not in response.headers


def test_rpc_post_no_origin_ok_but_doesnt_set_cors_headers(rpc_server, headers):
    headers.update({"Content-Type": "application/json"})
    response = rpc_server.fetch("/rpc", method="POST", body="hi", headers=headers)

    assert response.code == 200
    for k, _ in get_preflight_response_headers(headers):
        assert k not in response.headers


def test_rpc_post_with_origin_ok_sets_cors_headers(rpc_server, headers):
    headers.update(
        {"Content-Type": "application/json", "Origin": "http://foobar:6680"},
    )
    response = rpc_server.fetch("/rpc", method="POST", body="hi", headers=headers)

    assert response.code == 200
    assert_extra_response_headers(response.headers)
    for k, v in get_cors_response_headers(headers):
        assert response.headers[k] == v
    assert "Access-Control-Max-Age" not in response.headers


def test_rpc_no_csrf_options_no_origin_success(rpc_server_no_csrf, headers):
    response = rpc_server_no_csrf.fetch("/rpc", method="OPTIONS", headers=headers)

    assert response.code == 204


def test_rpc_no_csrf_post_no_content_type_ok(rpc_server_no_csrf, headers):
    response = rpc_server_no_csrf.fetch(
        "/rpc",
        method="POST",
        body="hi",
        headers=headers,
    )

    assert response.code == 200
    for k, _ in get_preflight_response_headers(headers):
        assert k not in response.headers


@pytest.fixture
def allowed():
    return set()


def test_check_origin_missing_origin_blocked(headers, allowed):
    assert not handlers.check_origin(None, headers, allowed)


def test_check_origin_empty_origin_allowed(headers, allowed):
    assert handlers.check_origin("", headers, allowed)


def test_check_origin_chrome_file_origin_allowed(headers, allowed):
    assert handlers.check_origin("file://", headers, allowed)


def test_check_origin_firefox_null_origin_allowed(headers, allowed):
    assert handlers.check_origin("null", headers, allowed)


def test_check_origin_same_host_origin_allowed(headers, allowed):
    assert handlers.check_origin("http://localhost:6680", headers, allowed)


def test_check_origin_different_host_origin_blocked(headers, allowed):
    assert not handlers.check_origin("http://other:6680", headers, allowed)


def test_check_origin_different_port_blocked(headers, allowed):
    assert not handlers.check_origin("http://localhost:80", headers, allowed)


def test_check_origin_extra_origin_allowed(headers, allowed):
    allowed.add("other:6680")
    assert handlers.check_origin("http://other:6680", headers, allowed)
