import json
import unittest
from typing import Any, Never
from unittest import mock

import msgspec
import pykka
import pytest

from mopidy import core, models
from mopidy.internal import deprecation, jsonrpc
from tests import dummy_backend


class Calculator:
    def __init__(self) -> None:
        self._mem = None

    def model(self) -> str:
        return "TI83"

    def add(self, a: int, b: int) -> int:
        """Returns the sum of the given numbers"""
        return a + b

    def sub(self, a: int, b: int) -> int:
        return a - b

    def set_mem(self, value: Any) -> None:
        self._mem = value

    def get_mem(self) -> Any | None:
        return self._mem

    def describe(self) -> dict[str, str]:
        return {
            "add": "Returns the sum of the terms",
            "sub": "Returns the diff of the terms",
        }

    def take_it_all(
        self,
        a: Any,
        b: Any,
        c: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        pass

    def _secret(self) -> str:
        return "Grand Unified Theory"

    def fail(self) -> Never:
        msg = "What did you expect?"
        raise ValueError(msg)


class JsonRpcTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = dummy_backend.create_proxy()
        self.calc = Calculator()

        with deprecation.ignore():
            self.core = core.Core.start(
                config={},
                backends=[self.backend],
            ).proxy()

        self.wrapper = jsonrpc.Wrapper(
            objects={
                "hello": lambda: "Hello, world!",
                "calc": self.calc,
                "core": self.core,
                "core.playback": self.core.playback,
                "core.tracklist": self.core.tracklist,
                "get_uri_schemes": self.core.get_uri_schemes,
            },
        )

    def tearDown(self) -> None:
        pykka.ActorRegistry.stop_all()


class JsonRpcSetupTest(JsonRpcTestBase):
    def test_empty_object_mounts_is_not_allowed(self) -> None:
        with pytest.raises(AttributeError):
            jsonrpc.Wrapper(objects={"": Calculator()})


class JsonRpcSerializationTest(JsonRpcTestBase):
    def test_handle_json_converts_from_and_to_json(self) -> None:
        self.wrapper.handle_data = mock.Mock()
        self.wrapper.handle_data.return_value = {"foo": "response"}

        request = '{"jsonrpc": "2.0", "method": "foo", "id": "1"}'
        response = self.wrapper.handle_json(request)

        self.wrapper.handle_data.assert_called_once_with(
            jsonrpc.Request.build(method="foo", id="1"),
        )
        assert response == b'{"foo":"response"}'

    def test_handle_json_decodes_mopidy_models(self) -> None:
        self.wrapper.handle_data = mock.Mock()
        self.wrapper.handle_data.return_value = []

        request = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "foo",
                "params": [
                    [  # A list of models as a single parameter
                        {"__model__": "Artist", "name": "foo"},
                        {"__model__": "Artist", "name": "bar"},
                    ],
                ],
                "id": "1",
            },
        )
        self.wrapper.handle_json(request)

        self.wrapper.handle_data.assert_called_once_with(
            jsonrpc.Request.build(
                method="foo",
                params=[
                    [
                        models.Artist(name="foo"),
                        models.Artist(name="bar"),
                    ],
                ],
                id="1",
            ),
        )

    def test_handle_json_encodes_mopidy_models(self) -> None:
        self.wrapper.handle_data = mock.Mock()
        self.wrapper.handle_data.return_value = {"foo": models.Artist(name="bar")}

        request = "[]"
        data = self.wrapper.handle_json(request)
        assert data
        response = json.loads(data.decode())

        assert "foo" in response
        assert "__model__" in response["foo"]
        assert response["foo"]["__model__"] == "Artist"
        assert "name" in response["foo"]
        assert response["foo"]["name"] == "bar"

    def test_handle_json_returns_nothing_for_notices(self) -> None:
        request = '{"jsonrpc": "2.0", "method": "core.get_uri_schemes"}'
        response = self.wrapper.handle_json(request)

        assert response is None

    def test_invalid_json_command_causes_parse_error(self) -> None:
        request = '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'
        response = self.wrapper.handle_json(request)
        assert response
        response = json.loads(response)

        assert response["jsonrpc"] == "2.0"
        error = response["error"]
        assert error["code"] == (-32700)
        assert error["message"] == "Parse error"

    def test_invalid_json_batch_causes_parse_error(self) -> None:
        request = """[
            {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
            {"jsonrpc": "2.0", "method"
        ]"""
        response = self.wrapper.handle_json(request)
        assert response
        response = json.loads(response)

        assert response == {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": (-32700),
                "message": "Parse error",
            },
        }


class JsonRpcSingleCommandTest(JsonRpcTestBase):
    def test_call_method_on_root(self) -> None:
        request = jsonrpc.Request.build(method="hello", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.id == 1
        assert response.result == "Hello, world!"
        assert response.error is msgspec.UNSET

    def test_call_method_on_plain_object(self) -> None:
        request = jsonrpc.Request.build(method="calc.model", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.id == 1
        assert response.result == "TI83"
        assert response.error is msgspec.UNSET

    def test_call_method_which_returns_dict_from_plain_object(self) -> None:
        request = jsonrpc.Request.build(method="calc.describe", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.result is not msgspec.UNSET
        assert "add" in response.result
        assert "sub" in response.result
        assert response.error is msgspec.UNSET

    def test_call_method_on_actor_root(self) -> None:
        request = jsonrpc.Request.build(method="core.get_uri_schemes", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.id == 1
        assert response.result == ["dummy"]
        assert response.error is msgspec.UNSET

    def test_call_method_on_actor_member(self) -> None:
        request = jsonrpc.Request.build(method="core.playback.get_time_position", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.result == 0
        assert response.error is msgspec.UNSET

    def test_call_method_which_is_a_directly_mounted_actor_member(self) -> None:
        # 'get_uri_schemes' isn't a regular callable, but a Pykka
        # CallableProxy. This test checks that CallableProxy objects are
        # threated by JsonRpcWrapper like any other callable.

        request = jsonrpc.Request.build(method="get_uri_schemes", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.id == 1
        assert response.result == ["dummy"]
        assert response.error is msgspec.UNSET

    def test_call_method_with_positional_params(self) -> None:
        request = jsonrpc.Request.build(method="calc.add", params=[3, 4], id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.result == 7
        assert response.error is msgspec.UNSET

    def test_call_method_with_named_params(self) -> None:
        request = jsonrpc.Request.build(
            method="calc.add",
            params={"a": 3, "b": 4},
            id=1,
        )
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.result == 7
        assert response.error is msgspec.UNSET

    def test_call_method_with_none_response(self) -> None:
        assert self.calc.get_mem() is None

        request = jsonrpc.Request.build(method="calc.set_mem", params=[37], id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.result is None

        json = msgspec.json.encode(response)
        assert json == b'{"jsonrpc":"2.0","id":1,"result":null}'


class JsonRpcSingleNotificationTest(JsonRpcTestBase):
    def test_notification_does_not_return_a_result(self) -> None:
        request = jsonrpc.Request.build(method="core.get_uri_schemes")
        response = self.wrapper.handle_data(request)

        assert response is None

    def test_notification_makes_an_observable_change(self) -> None:
        assert self.calc.get_mem() is None

        request = jsonrpc.Request.build(method="calc.set_mem", params=[37])
        response = self.wrapper.handle_data(request)

        assert response is None
        assert self.calc.get_mem() == 37

    def test_notification_unknown_method_returns_nothing(self) -> None:
        request = jsonrpc.Request.build(method="bogus", params=["bogus"])
        response = self.wrapper.handle_data(request)

        assert response is None


class JsonRpcBatchTest(JsonRpcTestBase):
    def test_batch_of_only_commands_returns_all(self) -> None:
        self.core.tracklist.set_random(True).get()

        request = [
            jsonrpc.Request.build(method="core.tracklist.get_repeat", id=1),
            jsonrpc.Request.build(method="core.tracklist.get_random", id=2),
            jsonrpc.Request.build(method="core.tracklist.get_single", id=3),
        ]
        response = self.wrapper.handle_data(request)

        assert isinstance(response, list)
        assert len(response) == 3

        response = {row.id: row for row in response if row.id is not None}
        assert response[1].result is False
        assert response[2].result is True
        assert response[3].result is False

    def test_batch_of_commands_and_notifications_returns_some(self) -> None:
        self.core.tracklist.set_random(True).get()

        request = [
            jsonrpc.Request.build(method="core.tracklist.get_repeat"),
            jsonrpc.Request.build(method="core.tracklist.get_random", id=2),
            jsonrpc.Request.build(method="core.tracklist.get_single", id=3),
        ]
        response = self.wrapper.handle_data(request)

        assert isinstance(response, list)
        assert len(response) == 2

        response = {row.id: row for row in response if row.id is not None}
        assert 1 not in response
        assert response[2].result is True
        assert response[3].result is False

    def test_batch_of_only_notifications_returns_nothing(self) -> None:
        self.core.tracklist.set_random(True).get()

        request = [
            jsonrpc.Request.build(method="core.tracklist.get_repeat"),
            jsonrpc.Request.build(method="core.tracklist.get_random"),
            jsonrpc.Request.build(method="core.tracklist.get_single"),
        ]
        response = self.wrapper.handle_data(request)

        assert response is None


class JsonRpcSingleCommandErrorTest(JsonRpcTestBase):
    def test_application_error_response(self) -> None:
        request = jsonrpc.Request.build(method="calc.fail", params=[], id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert response.result is msgspec.UNSET

        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == 0
        assert response.error.message == "Application error"

        data = response.error.data
        assert data is not None
        assert data["type"] == "ValueError"
        assert "What did you expect?" in data["message"]
        assert "traceback" in data
        assert "Traceback (most recent call last):" in data["traceback"]

    def test_missing_jsonrpc_member_causes_invalid_request_error(self) -> None:
        request = json.dumps(
            {
                "method": "core.get_uri_schemes",
                "id": 1,
            },
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Object missing required field `jsonrpc`"

    def test_wrong_jsonrpc_version_causes_invalid_request_error(self) -> None:
        request = json.dumps(
            {
                "jsonrpc": "3.0",
                "method": "core.get_uri_schemes",
                "id": 1,
            },
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Invalid enum value '3.0' - at `$.jsonrpc`"

    def test_missing_method_member_causes_invalid_request_error(self) -> None:
        request = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
            },
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Object missing required field `method`"

    def test_invalid_method_value_causes_invalid_request_error(self) -> None:
        request = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": 1,
                "id": 1,
            },
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Expected `str`, got `int` - at `$.method`"

    def test_invalid_params_value_causes_invalid_request_error(self) -> None:
        request = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "core.get_uri_schemes",
                "params": "foobar",
                "id": 1,
            },
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert (
            response.error.data
            == "Expected `object | array | null`, got `str` - at `$.params`"
        )

    def test_method_on_without_object_causes_unknown_method_error(self) -> None:
        request = jsonrpc.Request.build(method="bogus", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32601)
        assert response.error.message == "Method not found"
        assert (
            response.error.data == "Could not find object mount in method name 'bogus'"
        )

    def test_method_on_unknown_object_causes_unknown_method_error(self) -> None:
        request = jsonrpc.Request.build(method="bogus.bogus", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32601)
        assert response.error.message == "Method not found"
        assert response.error.data == "No object found at 'bogus'"

    def test_unknown_method_on_known_object_causes_unknown_method_error(self) -> None:
        request = jsonrpc.Request.build(method="core.bogus", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32601)
        assert response.error.message == "Method not found"
        assert response.error.data == "Object mounted at 'core' has no member 'bogus'"

    def test_private_method_causes_unknown_method_error(self) -> None:
        request = jsonrpc.Request.build(method="calc._secret", id=1)
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32601)
        assert response.error.message == "Method not found"
        assert response.error.data == "Private methods are not exported"

    def test_invalid_params_causes_invalid_params_error(self) -> None:
        request = jsonrpc.Request.build(
            method="core.get_uri_schemes",
            params=["bogus"],
            id=1,
        )
        response = self.wrapper.handle_data(request)

        assert isinstance(response, jsonrpc.Response)
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32602)
        assert response.error.message == "Invalid params"

        data = response.error.data
        assert data is not None
        assert data["type"] == "TypeError"
        assert (
            "get_uri_schemes() takes 1 positional argument but 2 were given"
            in data["message"]
        )
        assert "traceback" in data
        assert "Traceback (most recent call last):" in data["traceback"]


class JsonRpcBatchErrorTest(JsonRpcTestBase):
    def test_empty_batch_list_causes_invalid_request_error(self) -> None:
        request = json.dumps([])
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert isinstance(response, jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Batch list cannot be empty"

    def test_batch_with_invalid_request_causes_invalid_request_error(self) -> None:
        request = json.dumps([1])
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=jsonrpc.Response)
        assert response.id is None
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32600)
        assert response.error.message == "Invalid Request"
        assert response.error.data == "Expected `object`, got `int` - at `$[0]`"

    def test_batch_with_unknown_methods_causes_batch_of_errors(self) -> None:
        request = json.dumps(
            [
                {"jsonrpc": "2.0", "method": "does", "id": "1"},
                {"jsonrpc": "2.0", "method": "not", "id": "2"},
                {"jsonrpc": "2.0", "method": "exist", "id": "3"},
            ],
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=list[jsonrpc.Response])
        assert len(response) == 3
        response = response[2]
        assert response.id == "3"
        assert isinstance(response.error, jsonrpc.ErrorResponseDetails)
        assert response.error.code == (-32601)
        assert response.error.message == "Method not found"
        assert (
            response.error.data == "Could not find object mount in method name 'exist'"
        )

    def test_batch_of_both_successful_and_failing_requests(self) -> None:
        request = json.dumps(
            [
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
            ],
        )
        response = self.wrapper.handle_json(request)

        assert response
        response = msgspec.json.decode(response, type=list[jsonrpc.Response])
        assert len(response) == 4
        response = {row.id: row for row in response}
        assert response["1"].result is False
        assert response["2"].result is None
        assert isinstance(response["5"].error, jsonrpc.ErrorResponseDetails)
        assert response["5"].error.code == (-32601)
        assert response["9"].result is False


class JsonRpcInspectorTest(JsonRpcTestBase):
    def test_empty_object_mounts_is_not_allowed(self) -> None:
        with pytest.raises(AttributeError):
            jsonrpc.Inspector(objects={"": Calculator})

    def test_can_describe_method_on_root(self) -> None:
        inspector = jsonrpc.Inspector({"hello": lambda: "Hello, world!"})

        methods = inspector.describe()

        assert "hello" in methods
        assert len(methods["hello"].params) == 0

    def test_inspector_can_describe_an_object_with_methods(self) -> None:
        inspector = jsonrpc.Inspector({"calc": Calculator})

        methods = inspector.describe()

        assert "calc.add" in methods
        assert methods["calc.add"].description == "Returns the sum of the given numbers"

        assert "calc.sub" in methods
        assert "calc.take_it_all" in methods
        assert "calc._secret" not in methods
        assert "calc.__init__" not in methods

        method = methods["calc.take_it_all"]
        params = method.params

        assert params[0].name == "a"
        assert params[0].default is None

        assert params[1].name == "b"
        assert params[1].default is None

        assert params[2].name == "c"
        assert params[2].default is True

        assert params[3].name == "args"
        assert params[3].default is None
        assert params[3].varargs is True

        assert params[4].name == "kwargs"
        assert params[4].default is None
        assert params[4].kwargs is True

    def test_inspector_can_describe_a_bunch_of_large_classes(self) -> None:
        inspector = jsonrpc.Inspector(
            {
                "core.get_uri_schemes": core.Core.get_uri_schemes,
                "core.library": core.LibraryController,
                "core.playback": core.PlaybackController,
                "core.playlists": core.PlaylistsController,
                "core.tracklist": core.TracklistController,
            },
        )

        methods = inspector.describe()

        assert "core.get_uri_schemes" in methods
        assert len(methods["core.get_uri_schemes"].params) == 0

        assert "core.library.lookup" in methods
        assert methods["core.library.lookup"].params[0].name == "uris"

        assert "core.playback.next" in methods
        assert len(methods["core.playback.next"].params) == 0

        assert "core.playlists.as_list" in methods
        assert len(methods["core.playlists.as_list"].params) == 0

        assert "core.tracklist.filter" in methods
        assert methods["core.tracklist.filter"].params[0].name == "criteria"
