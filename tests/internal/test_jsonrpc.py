import json
import unittest
from unittest import mock

import pykka

from mopidy import core, models
from mopidy.internal import deprecation, jsonrpc

from tests import dummy_backend


class Calculator:
    def __init__(self):
        self._mem = None

    def model(self):
        return "TI83"

    def add(self, a, b):
        """Returns the sum of the given numbers"""
        return a + b

    def sub(self, a, b):
        return a - b

    def set_mem(self, value):
        self._mem = value

    def get_mem(self):
        return self._mem

    def describe(self):
        return {
            "add": "Returns the sum of the terms",
            "sub": "Returns the diff of the terms",
        }

    def take_it_all(self, a, b, c=True, *args, **kwargs):
        pass

    def _secret(self):
        return "Grand Unified Theory"

    def fail(self):
        raise ValueError("What did you expect?")


class JsonRpcTestBase(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.backend = dummy_backend.create_proxy()
        self.calc = Calculator()

        with deprecation.ignore():
            self.core = core.Core.start(backends=[self.backend]).proxy()

        self.jrw = jsonrpc.JsonRpcWrapper(
            objects={
                "hello": lambda: "Hello, world!",
                "calc": self.calc,
                "core": self.core,
                "core.playback": self.core.playback,
                "core.tracklist": self.core.tracklist,
                "get_uri_schemes": self.core.get_uri_schemes,
            },
            encoders=[models.ModelJSONEncoder],
            decoders=[models.model_json_decoder],
        )

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()


class JsonRpcSetupTest(JsonRpcTestBase):
    def test_empty_object_mounts_is_not_allowed(self):
        with self.assertRaises(AttributeError):
            jsonrpc.JsonRpcWrapper(objects={"": Calculator()})


class JsonRpcSerializationTest(JsonRpcTestBase):
    def test_handle_json_converts_from_and_to_json(self):
        self.jrw.handle_data = mock.Mock()
        self.jrw.handle_data.return_value = {"foo": "response"}

        request = '{"foo": "request"}'
        response = self.jrw.handle_json(request)

        self.jrw.handle_data.assert_called_once_with({"foo": "request"})
        assert response == '{"foo": "response"}'

    def test_handle_json_decodes_mopidy_models(self):
        self.jrw.handle_data = mock.Mock()
        self.jrw.handle_data.return_value = []

        request = '{"foo": {"__model__": "Artist", "name": "bar"}}'
        self.jrw.handle_json(request)

        self.jrw.handle_data.assert_called_once_with(
            {"foo": models.Artist(name="bar")}
        )

    def test_handle_json_encodes_mopidy_models(self):
        self.jrw.handle_data = mock.Mock()
        self.jrw.handle_data.return_value = {"foo": models.Artist(name="bar")}

        request = "[]"
        response = json.loads(self.jrw.handle_json(request))

        assert "foo" in response
        assert "__model__" in response["foo"]
        assert response["foo"]["__model__"] == "Artist"
        assert "name" in response["foo"]
        assert response["foo"]["name"] == "bar"

    def test_handle_json_returns_nothing_for_notices(self):
        request = '{"jsonrpc": "2.0", "method": "core.get_uri_schemes"}'
        response = self.jrw.handle_json(request)

        assert response is None

    def test_invalid_json_command_causes_parse_error(self):
        request = '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'
        response = self.jrw.handle_json(request)
        response = json.loads(response)

        assert response["jsonrpc"] == "2.0"
        error = response["error"]
        assert error["code"] == (-32700)
        assert error["message"] == "Parse error"

    def test_invalid_json_batch_causes_parse_error(self):
        request = """[
            {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
            {"jsonrpc": "2.0", "method"
        ]"""
        response = self.jrw.handle_json(request)
        response = json.loads(response)

        assert response["jsonrpc"] == "2.0"
        error = response["error"]
        assert error["code"] == (-32700)
        assert error["message"] == "Parse error"


class JsonRpcSingleCommandTest(JsonRpcTestBase):
    def test_call_method_on_root(self):
        request = {
            "jsonrpc": "2.0",
            "method": "hello",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" not in response
        assert response["result"] == "Hello, world!"

    def test_call_method_on_plain_object(self):
        request = {
            "jsonrpc": "2.0",
            "method": "calc.model",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" not in response
        assert response["result"] == "TI83"

    def test_call_method_which_returns_dict_from_plain_object(self):
        request = {
            "jsonrpc": "2.0",
            "method": "calc.describe",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" not in response
        assert "add" in response["result"]
        assert "sub" in response["result"]

    def test_call_method_on_actor_root(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core.get_uri_schemes",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" not in response
        assert response["result"] == ["dummy"]

    def test_call_method_on_actor_member(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core.playback.get_time_position",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["result"] == 0

    def test_call_method_which_is_a_directly_mounted_actor_member(self):
        # 'get_uri_schemes' isn't a regular callable, but a Pykka
        # CallableProxy. This test checks that CallableProxy objects are
        # threated by JsonRpcWrapper like any other callable.

        request = {
            "jsonrpc": "2.0",
            "method": "get_uri_schemes",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "error" not in response
        assert response["result"] == ["dummy"]

    def test_call_method_with_positional_params(self):
        request = {
            "jsonrpc": "2.0",
            "method": "calc.add",
            "params": [3, 4],
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["result"] == 7

    def test_call_methods_with_named_params(self):
        request = {
            "jsonrpc": "2.0",
            "method": "calc.add",
            "params": {"a": 3, "b": 4},
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["result"] == 7


class JsonRpcSingleNotificationTest(JsonRpcTestBase):
    def test_notification_does_not_return_a_result(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core.get_uri_schemes",
        }
        response = self.jrw.handle_data(request)

        assert response is None

    def test_notification_makes_an_observable_change(self):
        assert self.calc.get_mem() is None

        request = {
            "jsonrpc": "2.0",
            "method": "calc.set_mem",
            "params": [37],
        }
        response = self.jrw.handle_data(request)

        assert response is None
        assert self.calc.get_mem() == 37

    def test_notification_unknown_method_returns_nothing(self):
        request = {
            "jsonrpc": "2.0",
            "method": "bogus",
            "params": ["bogus"],
        }
        response = self.jrw.handle_data(request)

        assert response is None


class JsonRpcBatchTest(JsonRpcTestBase):
    def test_batch_of_only_commands_returns_all(self):
        self.core.tracklist.set_random(True).get()

        request = [
            {"jsonrpc": "2.0", "method": "core.tracklist.get_repeat", "id": 1},
            {"jsonrpc": "2.0", "method": "core.tracklist.get_random", "id": 2},
            {"jsonrpc": "2.0", "method": "core.tracklist.get_single", "id": 3},
        ]
        response = self.jrw.handle_data(request)

        assert len(response) == 3

        response = {row["id"]: row for row in response}
        assert response[1]["result"] is False
        assert response[2]["result"] is True
        assert response[3]["result"] is False

    def test_batch_of_commands_and_notifications_returns_some(self):
        self.core.tracklist.set_random(True).get()

        request = [
            {"jsonrpc": "2.0", "method": "core.tracklist.get_repeat"},
            {"jsonrpc": "2.0", "method": "core.tracklist.get_random", "id": 2},
            {"jsonrpc": "2.0", "method": "core.tracklist.get_single", "id": 3},
        ]
        response = self.jrw.handle_data(request)

        assert len(response) == 2

        response = {row["id"]: row for row in response}
        assert 1 not in response
        assert response[2]["result"] is True
        assert response[3]["result"] is False

    def test_batch_of_only_notifications_returns_nothing(self):
        self.core.tracklist.set_random(True).get()

        request = [
            {"jsonrpc": "2.0", "method": "core.tracklist.get_repeat"},
            {"jsonrpc": "2.0", "method": "core.tracklist.get_random"},
            {"jsonrpc": "2.0", "method": "core.tracklist.get_single"},
        ]
        response = self.jrw.handle_data(request)

        assert response is None


class JsonRpcSingleCommandErrorTest(JsonRpcTestBase):
    def test_application_error_response(self):
        request = {
            "jsonrpc": "2.0",
            "method": "calc.fail",
            "params": [],
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert "result" not in response

        error = response["error"]
        assert error["code"] == 0
        assert error["message"] == "Application error"

        data = error["data"]
        assert data["type"] == "ValueError"
        assert "What did you expect?" in data["message"]
        assert "traceback" in data
        assert "Traceback (most recent call last):" in data["traceback"]

    def test_missing_jsonrpc_member_causes_invalid_request_error(self):
        request = {
            "method": "core.get_uri_schemes",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "'jsonrpc' member must be included"

    def test_wrong_jsonrpc_version_causes_invalid_request_error(self):
        request = {
            "jsonrpc": "3.0",
            "method": "core.get_uri_schemes",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "'jsonrpc' value must be '2.0'"

    def test_missing_method_member_causes_invalid_request_error(self):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "'method' member must be included"

    def test_invalid_method_value_causes_invalid_request_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": 1,
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "'method' must be a string"

    def test_invalid_params_value_causes_invalid_request_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core.get_uri_schemes",
            "params": "foobar",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert (
            error["data"] == "'params', if given, must be an array or an object"
        )

    def test_method_on_without_object_causes_unknown_method_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": "bogus",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        error = response["error"]
        assert error["code"] == (-32601)
        assert error["message"] == "Method not found"
        assert (
            error["data"]
            == "Could not find object mount in method name 'bogus'"
        )

    def test_method_on_unknown_object_causes_unknown_method_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": "bogus.bogus",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        error = response["error"]
        assert error["code"] == (-32601)
        assert error["message"] == "Method not found"
        assert error["data"] == "No object found at 'bogus'"

    def test_unknown_method_on_known_object_causes_unknown_method_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core.bogus",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        error = response["error"]
        assert error["code"] == (-32601)
        assert error["message"] == "Method not found"
        assert error["data"] == "Object mounted at 'core' has no member 'bogus'"

    def test_private_method_causes_unknown_method_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core._secret",
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        error = response["error"]
        assert error["code"] == (-32601)
        assert error["message"] == "Method not found"
        assert error["data"] == "Private methods are not exported"

    def test_invalid_params_causes_invalid_params_error(self):
        request = {
            "jsonrpc": "2.0",
            "method": "core.get_uri_schemes",
            "params": ["bogus"],
            "id": 1,
        }
        response = self.jrw.handle_data(request)

        error = response["error"]
        assert error["code"] == (-32602)
        assert error["message"] == "Invalid params"

        data = error["data"]
        assert data["type"] == "TypeError"
        assert (
            data["message"]
            == "get_uri_schemes() takes 1 positional argument but 2 were given"
        )
        assert "traceback" in data
        assert "Traceback (most recent call last):" in data["traceback"]


class JsonRpcBatchErrorTest(JsonRpcTestBase):
    def test_empty_batch_list_causes_invalid_request_error(self):
        request = []
        response = self.jrw.handle_data(request)

        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "Batch list cannot be empty"

    def test_batch_with_invalid_command_causes_invalid_request_error(self):
        request = [1]
        response = self.jrw.handle_data(request)

        assert len(response) == 1
        response = response[0]
        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "Request must be an object"

    def test_batch_with_invalid_commands_causes_invalid_request_error(self):
        request = [1, 2, 3]
        response = self.jrw.handle_data(request)

        assert len(response) == 3
        response = response[2]
        assert response["id"] is None
        error = response["error"]
        assert error["code"] == (-32600)
        assert error["message"] == "Invalid Request"
        assert error["data"] == "Request must be an object"

    def test_batch_of_both_successfull_and_failing_requests(self):
        request = [
            # Call with positional params
            {
                "jsonrpc": "2.0",
                "method": "core.playback.seek",
                "params": [47],
                "id": "1",
            },
            # Notification
            {
                "jsonrpc": "2.0",
                "method": "core.tracklist.set_consume",
                "params": [True],
            },
            # Call with positional params
            {
                "jsonrpc": "2.0",
                "method": "core.tracklist.set_repeat",
                "params": [False],
                "id": "2",
            },
            # Invalid request
            {"foo": "boo"},
            # Unknown method
            {
                "jsonrpc": "2.0",
                "method": "foo.get",
                "params": {"name": "myself"},
                "id": "5",
            },
            # Call without params
            {
                "jsonrpc": "2.0",
                "method": "core.tracklist.get_random",
                "id": "9",
            },
        ]
        response = self.jrw.handle_data(request)

        assert len(response) == 5
        response = {row["id"]: row for row in response}
        assert response["1"]["result"] is False
        assert response["2"]["result"] is None
        assert response[None]["error"]["code"] == (-32600)
        assert response["5"]["error"]["code"] == (-32601)
        assert response["9"]["result"] is False


class JsonRpcInspectorTest(JsonRpcTestBase):
    def test_empty_object_mounts_is_not_allowed(self):
        with self.assertRaises(AttributeError):
            jsonrpc.JsonRpcInspector(objects={"": Calculator})

    def test_can_describe_method_on_root(self):
        inspector = jsonrpc.JsonRpcInspector({"hello": lambda: "Hello, world!"})

        methods = inspector.describe()

        assert "hello" in methods
        assert len(methods["hello"]["params"]) == 0

    def test_inspector_can_describe_an_object_with_methods(self):
        inspector = jsonrpc.JsonRpcInspector({"calc": Calculator})

        methods = inspector.describe()

        assert "calc.add" in methods
        assert (
            methods["calc.add"]["description"]
            == "Returns the sum of the given numbers"
        )

        assert "calc.sub" in methods
        assert "calc.take_it_all" in methods
        assert "calc._secret" not in methods
        assert "calc.__init__" not in methods

        method = methods["calc.take_it_all"]
        assert "params" in method

        params = method["params"]

        assert params[0]["name"] == "a"
        assert "default" not in params[0]

        assert params[1]["name"] == "b"
        assert "default" not in params[1]

        assert params[2]["name"] == "c"
        assert params[2]["default"] is True

        assert params[3]["name"] == "args"
        assert "default" not in params[3]
        assert params[3]["varargs"] is True

        assert params[4]["name"] == "kwargs"
        assert "default" not in params[4]
        assert params[4]["kwargs"] is True

    def test_inspector_can_describe_a_bunch_of_large_classes(self):
        inspector = jsonrpc.JsonRpcInspector(
            {
                "core.get_uri_schemes": core.Core.get_uri_schemes,
                "core.library": core.LibraryController,
                "core.playback": core.PlaybackController,
                "core.playlists": core.PlaylistsController,
                "core.tracklist": core.TracklistController,
            }
        )

        methods = inspector.describe()

        assert "core.get_uri_schemes" in methods
        assert len(methods["core.get_uri_schemes"]["params"]) == 0

        assert "core.library.lookup" in methods
        assert methods["core.library.lookup"]["params"][0]["name"] == "uris"

        assert "core.playback.next" in methods
        assert len(methods["core.playback.next"]["params"]) == 0

        assert "core.playlists.as_list" in methods
        assert len(methods["core.playlists.as_list"]["params"]) == 0

        assert "core.tracklist.filter" in methods
        assert (
            methods["core.tracklist.filter"]["params"][0]["name"] == "criteria"
        )
