import os
import unittest
from unittest import mock

import tornado.httpclient
import tornado.testing
import tornado.web
import tornado.websocket

import mopidy
from mopidy.http import handlers


class StaticFileHandlerTest(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        return tornado.web.Application(
            [
                (
                    r"/(.*)",
                    handlers.StaticFileHandler,
                    {
                        "path": os.path.dirname(__file__),
                        "default_filename": "test_handlers.py",
                    },
                )
            ]
        )

    def test_static_handler(self):
        response = self.fetch("/test_handlers.py", method="GET")

        assert 200 == response.code
        assert response.headers["X-Mopidy-Version"] == mopidy.__version__
        assert response.headers["Cache-Control"] == "no-cache"

    def test_static_default_filename(self):
        response = self.fetch("/", method="GET")

        assert 200 == response.code
        assert response.headers["X-Mopidy-Version"] == mopidy.__version__
        assert response.headers["Cache-Control"] == "no-cache"


class WebSocketHandlerTest(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        self.core = mock.Mock()
        return tornado.web.Application(
            [
                (
                    r"/ws/?",
                    handlers.WebSocketHandler,
                    {
                        "core": self.core,
                        "allowed_origins": frozenset(),
                        "csrf_protection": True,
                    },
                )
            ]
        )

    def connection(self, **kwargs):
        conn_kwargs = {
            "url": self.get_url("/ws").replace("http", "ws"),
        }
        conn_kwargs.update(kwargs)
        request = tornado.httpclient.HTTPRequest(**conn_kwargs)
        return tornado.websocket.websocket_connect(request)

    @tornado.testing.gen_test
    def test_invalid_json_rpc_request_doesnt_crash_handler(self):
        # An uncaught error would result in no message, so this is just a
        # simplistic test to verify this.
        conn = yield self.connection()
        conn.write_message("invalid request")
        message = yield conn.read_message()
        assert message

    @tornado.testing.gen_test
    def test_broadcast_makes_it_to_client(self):
        conn = yield self.connection()
        handlers.WebSocketHandler.broadcast("message", self.io_loop)
        message = yield conn.read_message()
        assert message == "message"

    @tornado.testing.gen_test
    def test_broadcast_to_client_that_just_closed_connection(self):
        conn = yield self.connection()
        conn.stream.close()
        handlers.WebSocketHandler.broadcast("message", self.io_loop)

    @tornado.testing.gen_test
    def test_broadcast_to_client_without_ws_connection_present(self):
        yield self.connection()
        # Tornado checks for ws_connection and raises WebSocketClosedError
        # if it is missing, this test case simulates winning a race were
        # this has happened but we have not yet been removed from clients.
        for client in handlers.WebSocketHandler.clients:
            client.ws_connection = None
        handlers.WebSocketHandler.broadcast("message", self.io_loop)

    @tornado.testing.gen_test
    def test_good_origin(self):
        headers = {"Origin": "http://localhost", "Host": "localhost"}
        conn = yield self.connection(headers=headers)
        assert conn

    @tornado.testing.gen_test
    def test_bad_origin(self):
        headers = {"Origin": "http://foobar", "Host": "localhost"}
        with self.assertRaises(tornado.httpclient.HTTPClientError) as e:
            _ = yield self.connection(headers=headers)
        assert e.exception.code == 403


class JsonRpcHandlerTestBase(tornado.testing.AsyncHTTPTestCase):
    csrf_protection = True

    def setUp(self):
        super().setUp()
        self.headers = {"Host": "localhost:6680"}

    def get_app(self):
        self.core = mock.Mock()
        return tornado.web.Application(
            [
                (
                    r"/rpc",
                    handlers.JsonRpcHandler,
                    {
                        "core": self.core,
                        "allowed_origins": set(),
                        "csrf_protection": self.csrf_protection,
                    },
                )
            ]
        )

    def assert_extra_response_headers(self, headers):
        assert headers["Cache-Control"] == "no-cache"
        assert headers["X-Mopidy-Version"] == mopidy.__version__
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json; utf-8"

    def get_cors_response_headers(self):
        yield (
            "Access-Control-Allow-Origin",
            self.headers.get("Origin"),
        )
        yield (
            "Access-Control-Allow-Headers",
            "Content-Type",
        )

    def test_head(self):
        response = self.fetch("/rpc", method="HEAD")

        assert response.code == 200
        self.assert_extra_response_headers(response.headers)


class JsonRpcHandlerTestCSRFEnabled(JsonRpcHandlerTestBase):
    def test_options_sets_cors_headers(self):
        self.headers.update({"Origin": "http://localhost:6680"})
        response = self.fetch("/rpc", method="OPTIONS", headers=self.headers)

        assert response.code == 204
        for k, v in self.get_cors_response_headers():
            self.assertEqual(response.headers[k], v)

    def test_options_bad_origin_forbidden(self):
        self.headers.update({"Origin": "http://foo:6680"})
        response = self.fetch("/rpc", method="OPTIONS", headers=self.headers)

        assert response.code == 403
        assert response.reason == "Access denied for origin http://foo:6680"
        for k, _ in self.get_cors_response_headers():
            self.assertNotIn(k, response.headers)

    def test_options_no_origin_forbidden(self):
        response = self.fetch("/rpc", method="OPTIONS", headers=self.headers)

        assert response.code == 403
        assert response.reason == "Access denied for origin None"
        for k, _ in self.get_cors_response_headers():
            self.assertNotIn(k, response.headers)

    def test_post_no_content_type_unsupported(self):
        response = self.fetch(
            "/rpc", method="POST", body="hi", headers=self.headers
        )

        assert response.code == 415
        for k, _ in self.get_cors_response_headers():
            self.assertNotIn(k, response.headers)

    def test_post_wrong_content_type_unsupported(self):
        self.headers.update({"Content-Type": "application/cats"})
        response = self.fetch(
            "/rpc", method="POST", body="hi", headers=self.headers
        )

        assert response.code == 415
        assert response.reason == "Content-Type must be application/json"
        for k, _ in self.get_cors_response_headers():
            self.assertNotIn(k, response.headers)

    def test_post_no_origin_ok_but_doesnt_set_cors_headers(self):
        self.headers.update({"Content-Type": "application/json"})
        response = self.fetch(
            "/rpc", method="POST", body="hi", headers=self.headers
        )

        assert response.code == 200
        for k, _ in self.get_cors_response_headers():
            self.assertNotIn(k, response.headers)

    def test_post_with_origin_ok_sets_cors_headers(self):
        self.headers.update(
            {"Content-Type": "application/json", "Origin": "http://foobar:6680"}
        )
        response = self.fetch(
            "/rpc", method="POST", body="hi", headers=self.headers
        )

        assert response.code == 200
        self.assert_extra_response_headers(response.headers)
        for k, v in self.get_cors_response_headers():
            self.assertEqual(response.headers[k], v)


class JsonRpcHandlerTestCSRFDisabled(JsonRpcHandlerTestBase):
    csrf_protection = False

    def test_options_no_origin_success(self):
        response = self.fetch("/rpc", method="OPTIONS", headers=self.headers)

        assert response.code == 204

    def test_post_no_content_type_ok(self):
        response = self.fetch(
            "/rpc", method="POST", body="hi", headers=self.headers
        )

        assert response.code == 200
        for k, _ in self.get_cors_response_headers():
            self.assertNotIn(k, response.headers)


class CheckOriginTests(unittest.TestCase):
    def setUp(self):
        self.headers = {"Host": "localhost:6680"}
        self.allowed = set()

    def test_missing_origin_blocked(self):
        assert not handlers.check_origin(None, self.headers, self.allowed)

    def test_empty_origin_allowed(self):
        assert handlers.check_origin("", self.headers, self.allowed)

    def test_chrome_file_origin_allowed(self):
        assert handlers.check_origin("file://", self.headers, self.allowed)

    def test_firefox_null_origin_allowed(self):
        assert handlers.check_origin("null", self.headers, self.allowed)

    def test_same_host_origin_allowed(self):
        assert handlers.check_origin(
            "http://localhost:6680", self.headers, self.allowed
        )

    def test_different_host_origin_blocked(self):
        assert not handlers.check_origin(
            "http://other:6680", self.headers, self.allowed
        )

    def test_different_port_blocked(self):
        assert not handlers.check_origin(
            "http://localhost:80", self.headers, self.allowed
        )

    def test_extra_origin_allowed(self):
        self.allowed.add("other:6680")
        assert handlers.check_origin(
            "http://other:6680", self.headers, self.allowed
        )
