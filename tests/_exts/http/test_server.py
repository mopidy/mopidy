import urllib
from pathlib import Path
from unittest import mock

import pytest
import tornado.escape
import tornado.web
import tornado.wsgi

import mopidy
from mopidy._exts.http import actor, handlers


def make_mopidy_app(**http_config):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "allowed_origins": frozenset(),
            "csrf_protection": True,
            "default_app": "mopidy",
            **http_config,
        },
    }
    core = mock.Mock()
    core.get_version = mock.MagicMock(name="get_version")
    core.get_version.return_value = mopidy.__version__

    testapps = [{"name": "testapp"}]
    teststatics = [{"name": "teststatic"}]

    apps = [
        {
            "name": "mopidy",
            "factory": handlers.make_mopidy_app_factory(
                apps=testapps,
                statics=teststatics,
            ),
        },
    ]

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=apps,
        statics=[],
    )

    return tornado.web.Application(http_server._get_request_handlers())


@pytest.fixture
def mopidy_server(tornado_server):
    return tornado_server(make_mopidy_app())


def test_root_should_redirect_to_mopidy_app(mopidy_server):
    response = mopidy_server.fetch("/", method="GET", follow_redirects=False)

    assert response.code == 302
    assert response.headers["Location"] == "/mopidy/"


def test_mopidy_app_should_return_index(mopidy_server):
    response = mopidy_server.fetch("/mopidy/", method="GET")
    body = response.body.decode()

    assert "This web server is a part of the Mopidy music server." in body
    assert "testapp" in body
    assert "teststatic" in body
    assert response.headers["X-Mopidy-Version"] == mopidy.__version__
    assert response.headers["Cache-Control"] == "no-cache"


def test_mopidy_app_without_slash_should_redirect(mopidy_server):
    response = mopidy_server.fetch("/mopidy", method="GET", follow_redirects=False)

    assert response.code == 301
    assert response.headers["Location"] == "/mopidy/"


def test_mopidy_app_should_return_static_files(mopidy_server):
    response = mopidy_server.fetch("/mopidy/mopidy.css", method="GET")

    assert "html {" in response.body.decode()
    assert response.headers["X-Mopidy-Version"] == mopidy.__version__
    assert response.headers["Cache-Control"] == "no-cache"


def test_ws_should_return_ws(mopidy_server):
    response = mopidy_server.fetch("/mopidy/ws", method="GET")

    assert response.body.decode() == 'Can "Upgrade" only to "WebSocket".'


def test_ws_should_return_ws_old(mopidy_server):
    response = mopidy_server.fetch("/mopidy/ws/", method="GET")

    assert response.body.decode() == 'Can "Upgrade" only to "WebSocket".'


def test_rpc_should_return_rpc_error(mopidy_server):
    cmd = tornado.escape.json_encode({"action": "get_version"})

    response = mopidy_server.fetch(
        "/mopidy/rpc",
        method="POST",
        body=cmd,
        headers={"Content-Type": "application/json"},
    )

    assert tornado.escape.json_decode(response.body) == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "message": "Invalid Request",
            "code": (-32600),
            "data": "'jsonrpc' member must be included",
        },
    }


def test_rpc_should_return_parse_error(mopidy_server):
    cmd = "{[[[]}"

    response = mopidy_server.fetch(
        "/mopidy/rpc",
        method="POST",
        body=cmd,
        headers={"Content-Type": "application/json"},
    )

    assert tornado.escape.json_decode(response.body) == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "message": "Parse error",
            "code": (-32700),
            "data": None,
        },
    }


def test_rpc_should_return_mopidy_version(mopidy_server):
    cmd = tornado.escape.json_encode(
        {
            "method": "core.get_version",
            "params": [],
            "jsonrpc": "2.0",
            "id": 1,
        },
    )

    response = mopidy_server.fetch(
        "/mopidy/rpc",
        method="POST",
        body=cmd,
        headers={"Content-Type": "application/json"},
    )

    assert tornado.escape.json_decode(response.body) == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": mopidy.__version__,
    }


@pytest.fixture
def mopidy_server_no_csrf(tornado_server):
    return tornado_server(make_mopidy_app(csrf_protection=False))


def get_cmd():
    return tornado.escape.json_encode(
        {
            "method": "core.get_version",
            "params": [],
            "jsonrpc": "2.0",
            "id": 1,
        },
    )


def test_rpc_no_csrf_should_ignore_incorrect_content_type(mopidy_server_no_csrf):
    response = mopidy_server_no_csrf.fetch(
        "/mopidy/rpc",
        method="POST",
        body=get_cmd(),
        headers={"Content-Type": "text/plain"},
    )

    assert response.code == 200


def test_rpc_no_csrf_should_ignore_missing_content_type(mopidy_server_no_csrf):
    response = mopidy_server_no_csrf.fetch(
        "/mopidy/rpc",
        method="POST",
        body=get_cmd(),
        headers={},
    )

    assert response.code == 200


def test_rpc_no_csrf_different_origin_returns_allowed(mopidy_server_no_csrf):
    response = mopidy_server_no_csrf.fetch(
        "/mopidy/rpc",
        method="OPTIONS",
        headers={"Host": "me:6680", "Origin": "http://evil:666"},
    )

    assert response.code == 204


def test_rpc_no_csrf_should_not_return_cors_headers(mopidy_server_no_csrf):
    response = mopidy_server_no_csrf.fetch(
        "/mopidy/rpc",
        method="OPTIONS",
        headers={"Host": "me:6680", "Origin": "http://me:6680"},
    )

    assert "Access-Control-Allow-Origin" not in response.headers
    assert "Access-Control-Allow-Headers" not in response.headers
    assert "Access-Control-Max-Age" not in response.headers


@pytest.fixture
def static_files_server(tornado_server):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "default_app": "static",
        },
    }
    core = mock.Mock()

    statics = [
        {
            "name": "static",
            "path": Path(__file__).parent,
        },
    ]

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=[],
        statics=statics,
    )

    return tornado_server(tornado.web.Application(http_server._get_request_handlers()))


def test_static_files_without_slash_should_redirect(static_files_server):
    response = static_files_server.fetch(
        "/static",
        method="GET",
        follow_redirects=False,
    )

    assert response.code == 301
    assert response.headers["Location"] == "/static/"


def test_static_files_can_serve_static_files(static_files_server):
    response = static_files_server.fetch("/static/test_server.py", method="GET")

    assert response.code == 200
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


@pytest.fixture
def wsgi_server(tornado_server):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "default_app": "wsgi",
        },
    }
    core = mock.Mock()

    apps = [{"name": "wsgi", "factory": wsgi_app_factory}]

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=apps,
        statics=[],
    )

    return tornado_server(tornado.web.Application(http_server._get_request_handlers()))


def test_wsgi_without_slash_should_redirect(wsgi_server):
    response = wsgi_server.fetch("/wsgi", method="GET", follow_redirects=False)

    assert response.code == 301
    assert response.headers["Location"] == "/wsgi/"


def test_wsgi_can_wrap_wsgi_apps(wsgi_server):
    response = wsgi_server.fetch("/wsgi/", method="GET")

    assert response.code == 200
    assert "Hello, world!" in response.body.decode()


def default_webapp_factory(config, core):
    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello from default webapp")

    return [("/", MainHandler, {})]


@pytest.fixture
def default_app_server(tornado_server):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "default_app": "default_app",
        },
    }
    core = mock.Mock()

    apps = [{"name": "default_app", "factory": default_webapp_factory}]

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=apps,
        statics=[],
    )

    return tornado_server(tornado.web.Application(http_server._get_request_handlers()))


def test_default_app_should_redirect_to_default_app(default_app_server):
    response = default_app_server.fetch("/", method="GET", follow_redirects=False)

    assert response.code == 302
    assert response.headers["Location"] == "/default_app/"

    response = default_app_server.fetch(
        "/default_app/",
        method="GET",
        follow_redirects=True,
    )

    assert response.code == 200
    assert "Hello from default webapp" in response.body.decode()


@pytest.fixture
def static_default_app_server(tornado_server):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "default_app": "default_app",
        },
    }
    core = mock.Mock()

    statics = [
        {
            "name": "default_app",
            "path": Path(__file__).parent,
        },
    ]

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=[],
        statics=statics,
    )

    return tornado_server(tornado.web.Application(http_server._get_request_handlers()))


def test_static_default_app_should_redirect_to_default_app(
    static_default_app_server,
):
    response = static_default_app_server.fetch(
        "/",
        method="GET",
        follow_redirects=False,
    )

    assert response.code == 302
    assert response.headers["Location"] == "/default_app/"


@pytest.fixture
def invalid_default_app_server(tornado_server):
    return tornado_server(make_mopidy_app(default_app="invalid_webclient"))


def test_invalid_default_app_should_redirect_to_clients_list(
    invalid_default_app_server,
):
    response = invalid_default_app_server.fetch(
        "/",
        method="GET",
        follow_redirects=False,
    )

    assert response.code == 302
    assert response.headers["Location"] == "/mopidy/"

    response = invalid_default_app_server.fetch("/", method="GET")
    body = response.body.decode()

    assert "This web server is a part of the Mopidy music server." in body

    assert "testapp" in body
    assert "teststatic" in body
    assert response.headers["X-Mopidy-Version"] == mopidy.__version__
    assert response.headers["Cache-Control"] == "no-cache"


def cookie_secret_app_factory(config, core):
    class BaseHandler(tornado.web.RequestHandler):
        def get_current_user(self):
            return self.get_secure_cookie("user")

    class LoginHandler(BaseHandler):
        def get(self):
            self.write("This is a login form")

        def post(self):
            self.set_secure_cookie("user", self.get_argument("name"))
            self.write("Logged in")

    class MainHandler(BaseHandler):
        def get(self):
            if not self.current_user:
                self.write("Unknown user...")
                return

            name = tornado.escape.xhtml_escape(self.current_user)
            self.write("Hello, " + name)

    return [("/", MainHandler, {}), ("/login", LoginHandler, {})]


@pytest.fixture
def secure_cookie_server(tornado_server, tmp_path):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "default_app": "mopidy",
        },
        "core": {"data_dir": tmp_path},
    }
    core = mock.Mock()

    apps = [
        {
            "name": "cookie_secret",
            "factory": cookie_secret_app_factory,
        },
    ]

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=apps,
        statics=[],
    )

    return tornado_server(
        tornado.web.Application(
            http_server._get_request_handlers(),
            cookie_secret=http_server._get_cookie_secret(),
        ),
    )


def test_secure_cookie_main_access_without_login(secure_cookie_server):
    response = secure_cookie_server.fetch("/cookie_secret", method="GET")

    assert response.code == 200
    assert "Unknown user..." in response.body.decode()


def test_secure_cookie_accessing_login_form_get(secure_cookie_server):
    response = secure_cookie_server.fetch("/cookie_secret/login", method="GET")

    assert response.code == 200
    assert "This is a login form" in response.body.decode()


def test_secure_cookie_login(secure_cookie_server):
    post_data = {"name": "theuser"}
    body = urllib.parse.urlencode(post_data)

    response = secure_cookie_server.fetch(
        "/cookie_secret/login",
        method="POST",
        body=body,
    )

    assert response.code == 200
    assert "Logged in" in response.body.decode()


def test_get_secure_cookie(tmp_path):
    config = {
        "http": {
            "hostname": "127.0.0.1",
            "port": 6680,
            "zeroconf": "",
            "default_app": "mopidy",
        },
        "core": {"data_dir": tmp_path},
    }
    core = mock.Mock()

    http_server = actor.HttpServer(
        config=config,
        core=core,
        sockets=[],
        apps=[],
        statics=[],
    )

    # first secret, generating
    secret_1 = http_server._get_cookie_secret()

    assert isinstance(secret_1, str)
    assert secret_1 != ""
    assert len(secret_1) == 64

    # second secret, from file
    secret_2 = http_server._get_cookie_secret()
    assert secret_1 == secret_2
