import json
from collections.abc import Iterator
from typing import Any, Never, cast
from unittest import mock

import pykka
import pytest

from mopidy import models
from mopidy._exts.http import jsonrpc
from mopidy.core import (
    Core,
    CoreProxy,
    LibraryController,
    PlaybackController,
    PlaylistsController,
    TracklistController,
)
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
        d: Any,
        e: bool = False,
        **kwargs: Any,
    ) -> None:
        pass

    def _secret(self) -> str:
        return "Grand Unified Theory"

    def fail(self) -> Never:
        msg = "What did you expect?"
        raise ValueError(msg)


@pytest.fixture
def backend() -> pykka.ActorProxy[dummy_backend.DummyBackend]:
    return dummy_backend.create_proxy()


@pytest.fixture
def calc() -> Calculator:
    return Calculator()


@pytest.fixture
def core(backend: pykka.ActorProxy[dummy_backend.DummyBackend]) -> Iterator[CoreProxy]:
    yield cast(
        CoreProxy,
        Core.start(
            config={},
            backends=[backend],
        ).proxy(),
    )
    pykka.ActorRegistry.stop_all()


@pytest.fixture
def wrapper(calc: Calculator, core: CoreProxy) -> jsonrpc.Wrapper:
    return jsonrpc.Wrapper(
        objects={
            "hello": lambda: "Hello, world!",
            "calc": calc,
            "core": core,
            "core.playback": core.playback,
            "core.tracklist": core.tracklist,
            "get_uri_schemes": core.get_uri_schemes,
        },
    )


def test_setup_empty_object_mounts_is_not_allowed() -> None:
    with pytest.raises(AttributeError):
        jsonrpc.Wrapper(objects={"": Calculator()})


def test_serialization_handle_json_converts_from_and_to_json(
    wrapper: jsonrpc.Wrapper,
) -> None:
    wrapper.handle_data = mock.Mock()
    wrapper.handle_data.return_value = jsonrpc.SuccessResponse(id=1, result="foo")

    request = b'{"foo": "request"}'
    response = wrapper.handle_json(request)

    wrapper.handle_data.assert_called_once_with({"foo": "request"})
    assert response == b'{"jsonrpc":"2.0","id":1,"result":"foo"}'


def test_serialization_request_decoding_decodes_mopidy_models() -> None:
    request_dict = {
        "jsonrpc": "2.0",
        "method": "calc.set_mem",
        "params": [{"__model__": "Artist", "name": "bar"}],
    }

    request = jsonrpc.Request.model_validate(request_dict)

    assert isinstance(request.params, list)
    assert request.params[0] == models.Artist(name="bar")


def test_serialization_request_decoding_decodes_nested_mopidy_models() -> None:
    request_dict = {
        "jsonrpc": "2.0",
        "method": "core.tracklist.add",
        "params": {
            "tracks": [
                {"__model__": "Track", "uri": "dummy:uri", "name": "Test"},
            ],
        },
    }

    request = jsonrpc.Request.model_validate(request_dict)

    assert isinstance(request.params, dict)
    tracks = request.params["tracks"]
    assert isinstance(tracks, list)
    assert len(tracks) == 1
    assert isinstance(tracks[0], models.Track)
    assert tracks[0].uri == "dummy:uri"
    assert tracks[0].name == "Test"


def test_serialization_handle_json_encodes_mopidy_models(
    wrapper: jsonrpc.Wrapper,
) -> None:
    wrapper.handle_data = mock.Mock()
    wrapper.handle_data.return_value = jsonrpc.SuccessResponse(
        id=1,
        result=models.Artist(name="bar"),
    )

    request = "[]"
    response = wrapper.handle_json(request)

    assert response is not None
    response = json.loads(response)
    assert "result" in response
    assert "__model__" in response["result"]
    assert response["result"]["__model__"] == "Artist"
    assert "name" in response["result"]
    assert response["result"]["name"] == "bar"


def test_serialization_handle_json_returns_nothing_for_notices(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = '{"jsonrpc": "2.0", "method": "core.get_uri_schemes"}'
    response = wrapper.handle_json(request)

    assert response is None


def test_serialization_invalid_json_command_causes_parse_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'
    response = wrapper.handle_json(request)

    assert response is not None
    response = json.loads(response)
    assert response["jsonrpc"] == "2.0"
    error = response["error"]
    assert error["code"] == (-32700)
    assert error["message"] == "Parse error"


def test_serialization_invalid_json_batch_causes_parse_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = """[
        {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
        {"jsonrpc": "2.0", "method"
    ]"""
    response = wrapper.handle_json(request)

    assert response is not None
    response = json.loads(response)
    assert response["jsonrpc"] == "2.0"
    error = response["error"]
    assert error["code"] == (-32700)
    assert error["message"] == "Parse error"


def test_single_command_call_method_on_root(wrapper: jsonrpc.Wrapper) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "hello",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.jsonrpc == "2.0"
    assert response.id == 1
    assert response.result == "Hello, world!"


def test_single_command_call_method_on_plain_object(wrapper: jsonrpc.Wrapper) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "calc.model",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.result == "TI83"


def test_single_command_call_method_which_returns_dict_from_plain_object(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "calc.describe",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert "add" in response.result
    assert "sub" in response.result


def test_single_command_call_method_on_actor_root(wrapper: jsonrpc.Wrapper) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core.get_uri_schemes",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.result == ["dummy"]


def test_single_command_call_method_on_actor_member(wrapper: jsonrpc.Wrapper) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core.playback.get_time_position",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.result == 0


def test_single_command_call_method_which_is_a_directly_mounted_actor_member(
    wrapper: jsonrpc.Wrapper,
) -> None:
    # 'get_uri_schemes' isn't a regular callable, but a Pykka
    # CallableProxy. This test checks that CallableProxy objects are
    # threated by JsonRpcWrapper like any other callable.

    request = {
        "jsonrpc": "2.0",
        "method": "get_uri_schemes",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.result == ["dummy"]


def test_single_command_call_method_with_positional_params(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "calc.add",
        "params": [3, 4],
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.result == 7


def test_single_command_call_method_with_named_params(wrapper: jsonrpc.Wrapper) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "calc.add",
        "params": {"a": 3, "b": 4},
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.SuccessResponse)
    assert response.result == 7


def test_single_notification_does_not_return_a_result(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core.get_uri_schemes",
    }
    response = wrapper.handle_data(request)

    assert response is None


def test_single_notification_makes_an_observable_change(
    wrapper: jsonrpc.Wrapper, calc: Calculator
) -> None:
    assert calc.get_mem() is None

    request = {
        "jsonrpc": "2.0",
        "method": "calc.set_mem",
        "params": [37],
    }
    response = wrapper.handle_data(request)

    assert response is None
    assert calc.get_mem() == 37


def test_single_notification_unknown_method_returns_nothing(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "bogus",
        "params": ["bogus"],
    }
    response = wrapper.handle_data(request)

    assert response is None


def test_batch_of_only_commands_returns_all(
    wrapper: jsonrpc.Wrapper, core: CoreProxy
) -> None:
    core.tracklist.set_random(True).get()

    request = [
        {"jsonrpc": "2.0", "method": "core.tracklist.get_repeat", "id": 1},
        {"jsonrpc": "2.0", "method": "core.tracklist.get_random", "id": 2},
        {"jsonrpc": "2.0", "method": "core.tracklist.get_single", "id": 3},
    ]
    response = wrapper.handle_data(request)

    assert isinstance(response, list)
    assert len(response) == 3
    response_1, response_2, response_3 = response
    assert isinstance(response_1, jsonrpc.SuccessResponse)
    assert response_1.result is False
    assert isinstance(response_2, jsonrpc.SuccessResponse)
    assert response_2.result is True
    assert isinstance(response_3, jsonrpc.SuccessResponse)
    assert response_3.result is False


def test_batch_of_commands_and_notifications_returns_some(
    wrapper: jsonrpc.Wrapper, core: CoreProxy
) -> None:
    core.tracklist.set_random(True).get()

    request = [
        {"jsonrpc": "2.0", "method": "core.tracklist.get_repeat"},
        {"jsonrpc": "2.0", "method": "core.tracklist.get_random", "id": 2},
        {"jsonrpc": "2.0", "method": "core.tracklist.get_single", "id": 3},
    ]
    response = wrapper.handle_data(request)

    assert isinstance(response, list)
    assert len(response) == 2

    response_2, response_3 = response
    assert isinstance(response_2, jsonrpc.SuccessResponse)
    assert response_2.id == 2
    assert response_2.result is True
    assert isinstance(response_3, jsonrpc.SuccessResponse)
    assert response_3.id == 3
    assert response_3.result is False


def test_batch_of_only_notifications_returns_nothing(
    wrapper: jsonrpc.Wrapper, core: CoreProxy
) -> None:
    core.tracklist.set_random(True).get()
    request = [
        {"jsonrpc": "2.0", "method": "core.tracklist.get_repeat"},
        {"jsonrpc": "2.0", "method": "core.tracklist.get_random"},
        {"jsonrpc": "2.0", "method": "core.tracklist.get_single"},
    ]

    response = wrapper.handle_data(request)

    assert response is None


def test_single_command_error_application_error_response(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "calc.fail",
        "params": [],
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.error.code == 0
    assert response.error.message == "Application error"

    data = response.error.data
    assert isinstance(data, dict)
    assert data["type"] == "ValueError"
    assert "What did you expect?" in data["message"]
    assert "traceback" in data
    assert "Traceback (most recent call last):" in data["traceback"]


def test_single_command_error_missing_jsonrpc_member_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "method": "core.get_uri_schemes",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.id is None
    assert response.error.code == (-32600)
    assert response.error.message == "Invalid Request"
    assert response.error.data == "'jsonrpc' member must be included"


def test_single_command_error_wrong_jsonrpc_version_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "3.0",
        "method": "core.get_uri_schemes",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.id is None
    assert response.error.code == (-32600)
    assert response.error.message == "Invalid Request"
    assert response.error.data == "'jsonrpc' value must be '2.0'"


def test_single_command_error_missing_method_member_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.id is None
    assert response.error.code == (-32600)
    assert response.error.message == "Invalid Request"
    assert response.error.data == "'method' member must be included"


def test_single_command_error_invalid_method_value_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": 1,
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.id is None
    assert response.error.code == (-32600)
    assert response.error.message == "Invalid Request"
    assert response.error.data == "'method' must be a string"


def test_single_command_error_invalid_params_value_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core.get_uri_schemes",
        "params": "foobar",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.id is None
    assert response.error.code == (-32600)
    assert response.error.message == "Invalid Request"
    assert response.error.data == "'params', if given, must be an array or an object"


def test_single_command_error_method_on_without_object_causes_unknown_method_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "bogus",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.error.code == (-32601)
    assert response.error.message == "Method not found"
    assert response.error.data == "Could not find object mount in method name 'bogus'"


def test_single_command_error_method_on_unknown_object_causes_unknown_method_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "bogus.bogus",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.error.code == (-32601)
    assert response.error.message == "Method not found"
    assert response.error.data == "No object found at 'bogus'"


def test_single_command_error_unknown_method_on_known_object(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core.bogus",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.error.code == (-32601)
    assert response.error.message == "Method not found"
    assert response.error.data == "Object mounted at 'core' has no member 'bogus'"


def test_single_command_error_private_method_causes_unknown_method_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core._secret",
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.error.code == (-32601)
    assert response.error.message == "Method not found"
    assert response.error.data == "Private methods are not exported"


def test_single_command_error_invalid_params_causes_invalid_params_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "core.get_uri_schemes",
        "params": ["bogus"],
        "id": 1,
    }
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.ErrorResponse)
    assert response.error.code == (-32602)
    assert response.error.message == "Invalid params"

    data = response.error.data
    assert isinstance(data, dict)
    assert data["type"] == "TypeError"
    assert (
        "get_uri_schemes() takes 1 positional argument but 2 were given"
        in data["message"]
    )
    assert "traceback" in data
    assert "Traceback (most recent call last):" in data["traceback"]


def test_batch_error_empty_batch_list_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = []
    response = wrapper.handle_data(request)

    assert isinstance(response, jsonrpc.Response)
    assert response.id is None
    assert response.error.code == (-32600)
    assert response.error.message == "Invalid Request"
    assert response.error.data == "Batch list cannot be empty"


def test_batch_error_batch_with_invalid_command_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = [1]
    response = wrapper.handle_data(request)

    assert isinstance(response, list)
    assert len(response) == 1
    assert response[0].id is None
    assert response[0].error.code == (-32600)
    assert response[0].error.message == "Invalid Request"
    assert response[0].error.data == "Request must be an object"


def test_batch_error_batch_with_invalid_commands_causes_invalid_request_error(
    wrapper: jsonrpc.Wrapper,
) -> None:
    request = [1, 2, 3]
    response = wrapper.handle_data(request)

    assert isinstance(response, list)
    assert len(response) == 3
    assert response[2].id is None
    assert response[2].error.code == (-32600)
    assert response[2].error.message == "Invalid Request"
    assert response[2].error.data == "Request must be an object"


def test_batch_error_batch_of_both_successful_and_failing_requests(
    wrapper: jsonrpc.Wrapper,
) -> None:
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

    response = wrapper.handle_data(request)

    assert isinstance(response, list)
    assert len(response) == 5
    response_1, response_2, response_none, response_5, response_9 = response
    assert isinstance(response_1, jsonrpc.SuccessResponse)
    assert response_1.id == "1"
    assert response_1.result is False
    assert isinstance(response_2, jsonrpc.SuccessResponse)
    assert response_2.id == "2"
    assert response_2.result is None
    assert isinstance(response_none, jsonrpc.ErrorResponse)
    assert response_none.id is None
    assert response_none.error.code == (-32600)
    assert isinstance(response_5, jsonrpc.ErrorResponse)
    assert response_5.id == "5"
    assert response_5.error.code == (-32601)
    assert isinstance(response_9, jsonrpc.SuccessResponse)
    assert response_9.id == "9"
    assert response_9.result is False


def test_inspector_empty_object_mounts_is_not_allowed() -> None:
    with pytest.raises(AttributeError):
        jsonrpc.Inspector(objects={"": Calculator})


def test_inspector_can_describe_method_on_root() -> None:
    inspector = jsonrpc.Inspector({"hello": lambda: "Hello, world!"})

    methods = inspector.describe()

    assert "hello" in methods
    assert len(methods["hello"].params) == 0


def test_inspector_can_describe_an_object_with_methods() -> None:
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
    assert params[0].default is jsonrpc.Unset
    assert params[0].model_dump_json() == '{"name":"a"}'

    assert params[1].name == "b"
    assert params[1].default is jsonrpc.Unset
    assert params[1].model_dump_json() == '{"name":"b"}'

    assert params[2].name == "c"
    assert params[2].default is True
    assert params[2].model_dump_json() == '{"name":"c","default":true}'

    assert params[3].name == "args"
    assert params[3].default is jsonrpc.Unset
    assert params[3].varargs is True
    assert params[3].model_dump_json() == '{"name":"args","varargs":true}'

    assert params[4].name == "d"
    assert params[4].default is jsonrpc.Unset
    assert params[4].model_dump_json() == '{"name":"d"}'

    assert params[5].name == "e"
    assert params[5].default is False
    assert params[5].model_dump_json() == '{"name":"e","default":false}'

    assert params[6].name == "kwargs"
    assert params[6].default is jsonrpc.Unset
    assert params[6].kwargs is True
    assert params[6].model_dump_json() == '{"name":"kwargs","kwargs":true}'


def test_inspector_can_describe_a_bunch_of_large_classes() -> None:
    inspector = jsonrpc.Inspector(
        {
            "core.get_uri_schemes": Core.get_uri_schemes,
            "core.library": LibraryController,
            "core.playback": PlaybackController,
            "core.playlists": PlaylistsController,
            "core.tracklist": TracklistController,
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

    # Keyword-only params are described too
    assert "core.tracklist.add" in methods
    assert [p.name for p in methods["core.tracklist.add"].params] == [
        "tracks",
        "at_position",
        "uris",
    ]

    # Deprecated methods are described with their own params, not with the
    # params of the wrapper added by the `deprecated` decorator
    assert "core.tracklist.eot_track" in methods
    assert [p.name for p in methods["core.tracklist.eot_track"].params] == [
        "tl_track",
    ]
