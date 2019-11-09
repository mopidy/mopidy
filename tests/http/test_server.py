import os
from unittest import mock

import tornado.testing
import tornado.wsgi

import mopidy
from mopidy.http import actor, handlers


class HttpServerTest(tornado.testing.AsyncHTTPTestCase):
    def get_config(self):
        return {
            "http": {
                "hostname": "127.0.0.1",
                "port": 6680,
                "zeroconf": "",
                "allowed_origins": [],
                "csrf_protection": True,
            }
        }

    def get_app(self):
        core = mock.Mock()
        core.get_version = mock.MagicMock(name="get_version")
        core.get_version.return_value = mopidy.__version__

        testapps = [dict(name="testapp")]
        teststatics = [dict(name="teststatic")]

        apps = [
            {
                "name": "mopidy",
                "factory": handlers.make_mopidy_app_factory(
                    testapps, teststatics
                ),
            }
        ]

        http_server = actor.HttpServer(
            config=self.get_config(),
            core=core,
            sockets=[],
            apps=apps,
            statics=[],
        )

        return tornado.web.Application(http_server._get_request_handlers())


class RootRedirectTest(HttpServerTest):
    def test_should_redirect_to_mopidy_app(self):
        response = self.fetch("/", method="GET", follow_redirects=False)

        assert response.code == 302
        assert response.headers["Location"] == "/mopidy/"


class MopidyAppTest(HttpServerTest):
    def test_should_return_index(self):
        response = self.fetch("/mopidy/", method="GET")
        body = tornado.escape.to_unicode(response.body)

        assert "This web server is a part of the Mopidy music server." in body
        assert "testapp" in body
        assert "teststatic" in body
        assert response.headers["X-Mopidy-Version"] == mopidy.__version__
        assert response.headers["Cache-Control"] == "no-cache"

    def test_without_slash_should_redirect(self):
        response = self.fetch("/mopidy", method="GET", follow_redirects=False)

        assert response.code == 301
        assert response.headers["Location"] == "/mopidy/"

    def test_should_return_static_files(self):
        response = self.fetch("/mopidy/mopidy.css", method="GET")

        assert "html {" in tornado.escape.to_unicode(response.body)
        assert response.headers["X-Mopidy-Version"] == mopidy.__version__
        assert response.headers["Cache-Control"] == "no-cache"


class MopidyWebSocketHandlerTest(HttpServerTest):
    def test_should_return_ws(self):
        response = self.fetch("/mopidy/ws", method="GET")

        assert (
            'Can "Upgrade" only to "WebSocket".'
            == tornado.escape.to_unicode(response.body)
        )

    def test_should_return_ws_old(self):
        response = self.fetch("/mopidy/ws/", method="GET")

        assert (
            'Can "Upgrade" only to "WebSocket".'
            == tornado.escape.to_unicode(response.body)
        )


class MopidyRPCHandlerTest(HttpServerTest):
    def test_should_return_rpc_error(self):
        cmd = tornado.escape.json_encode({"action": "get_version"})

        response = self.fetch(
            "/mopidy/rpc",
            method="POST",
            body=cmd,
            headers={"Content-Type": "application/json"},
        )

        assert {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "message": "Invalid Request",
                "code": (-32600),
                "data": "'jsonrpc' member must be included",
            },
        } == tornado.escape.json_decode(response.body)

    def test_should_return_parse_error(self):
        cmd = "{[[[]}"

        response = self.fetch(
            "/mopidy/rpc",
            method="POST",
            body=cmd,
            headers={"Content-Type": "application/json"},
        )

        assert {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"message": "Parse error", "code": (-32700)},
        } == tornado.escape.json_decode(response.body)

    def test_should_return_mopidy_version(self):
        cmd = tornado.escape.json_encode(
            {
                "method": "core.get_version",
                "params": [],
                "jsonrpc": "2.0",
                "id": 1,
            }
        )

        response = self.fetch(
            "/mopidy/rpc",
            method="POST",
            body=cmd,
            headers={"Content-Type": "application/json"},
        )

        assert {
            "jsonrpc": "2.0",
            "id": 1,
            "result": mopidy.__version__,
        } == tornado.escape.json_decode(response.body)

    def test_should_return_extra_headers(self):
        response = self.fetch("/mopidy/rpc", method="HEAD")

        assert "Accept" in response.headers
        assert "X-Mopidy-Version" in response.headers
        assert "Cache-Control" in response.headers
        assert "Content-Type" in response.headers

    def test_should_require_correct_content_type(self):
        cmd = tornado.escape.json_encode(
            {
                "method": "core.get_version",
                "params": [],
                "jsonrpc": "2.0",
                "id": 1,
            }
        )

        response = self.fetch(
            "/mopidy/rpc",
            method="POST",
            body=cmd,
            headers={"Content-Type": "text/plain"},
        )

        assert response.code == 415
        assert response.reason == "Content-Type must be application/json"

    def test_different_origin_returns_access_denied(self):
        response = self.fetch(
            "/mopidy/rpc",
            method="OPTIONS",
            headers={"Host": "me:6680", "Origin": "http://evil:666"},
        )

        assert response.code == 403
        assert response.reason == "Access denied for origin http://evil:666"

    def test_same_origin_returns_cors_headers(self):
        response = self.fetch(
            "/mopidy/rpc",
            method="OPTIONS",
            headers={"Host": "me:6680", "Origin": "http://me:6680"},
        )

        assert (
            response.headers["Access-Control-Allow-Origin"] == "http://me:6680"
        )
        assert (
            response.headers["Access-Control-Allow-Headers"] == "Content-Type"
        )


class MopidyRPCHandlerNoCSRFProtectionTest(HttpServerTest):
    def get_config(self):
        config = super().get_config()
        config["http"]["csrf_protection"] = False
        return config

    def get_cmd(self):
        return tornado.escape.json_encode(
            {
                "method": "core.get_version",
                "params": [],
                "jsonrpc": "2.0",
                "id": 1,
            }
        )

    def test_should_ignore_incorrect_content_type(self):
        response = self.fetch(
            "/mopidy/rpc",
            method="POST",
            body=self.get_cmd(),
            headers={"Content-Type": "text/plain"},
        )

        assert response.code == 200

    def test_should_ignore_missing_content_type(self):
        response = self.fetch(
            "/mopidy/rpc", method="POST", body=self.get_cmd(), headers={}
        )

        assert response.code == 200

    def test_different_origin_returns_allowed(self):
        response = self.fetch(
            "/mopidy/rpc",
            method="OPTIONS",
            headers={"Host": "me:6680", "Origin": "http://evil:666"},
        )

        assert response.code == 204

    def test_should_not_return_cors_headers(self):
        response = self.fetch(
            "/mopidy/rpc",
            method="OPTIONS",
            headers={"Host": "me:6680", "Origin": "http://me:6680"},
        )

        assert "Access-Control-Allow-Origin" not in response.headers
        assert "Access-Control-Allow-Headers" not in response.headers


class HttpServerWithStaticFilesTest(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        config = {
            "http": {"hostname": "127.0.0.1", "port": 6680, "zeroconf": ""}
        }
        core = mock.Mock()

        statics = [dict(name="static", path=os.path.dirname(__file__))]

        http_server = actor.HttpServer(
            config=config, core=core, sockets=[], apps=[], statics=statics
        )

        return tornado.web.Application(http_server._get_request_handlers())

    def test_without_slash_should_redirect(self):
        response = self.fetch("/static", method="GET", follow_redirects=False)

        assert response.code == 301
        assert response.headers["Location"] == "/static/"

    def test_can_serve_static_files(self):
        response = self.fetch("/static/test_server.py", method="GET")

        assert 200 == response.code
        assert response.headers["X-Mopidy-Version"] == mopidy.__version__
        assert response.headers["Cache-Control"] == "no-cache"


def wsgi_app_factory(config, core):
    def wsgi_app(environ, start_response):
        status = "200 OK"
        response_headers = [("Content-type", "text/plain")]
        start_response(status, response_headers)
        return [b"Hello, world!\n"]

    return [
        (
            "(.*)",
            tornado.web.FallbackHandler,
            {"fallback": tornado.wsgi.WSGIContainer(wsgi_app)},
        ),
    ]


class HttpServerWithWsgiAppTest(tornado.testing.AsyncHTTPTestCase):
    def get_app(self):
        config = {
            "http": {"hostname": "127.0.0.1", "port": 6680, "zeroconf": ""}
        }
        core = mock.Mock()

        apps = [{"name": "wsgi", "factory": wsgi_app_factory}]

        http_server = actor.HttpServer(
            config=config, core=core, sockets=[], apps=apps, statics=[]
        )

        return tornado.web.Application(http_server._get_request_handlers())

    def test_without_slash_should_redirect(self):
        response = self.fetch("/wsgi", method="GET", follow_redirects=False)

        assert response.code == 301
        assert response.headers["Location"] == "/wsgi/"

    def test_can_wrap_wsgi_apps(self):
        response = self.fetch("/wsgi/", method="GET")

        assert 200 == response.code
        assert "Hello, world!" in tornado.escape.to_unicode(response.body)
