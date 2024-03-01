import inspect
import json
import traceback
from collections.abc import Callable
from typing import Any, Literal, TypeAlias, TypedDict, TypeVar

import pykka

T = TypeVar("T")


class JsonRpcNotification(TypedDict):
    jsonrpc: Literal["2.0"]
    method: str
    params: list[Any] | dict[str, Any]


JsonRpcRequestId: TypeAlias = str | int | float


class JsonRpcRequest(JsonRpcNotification):
    id: JsonRpcRequestId | None


class JsonRpcErrorDetails(TypedDict, total=False):
    code: int
    message: str
    data: Any | None


class JsonRpcErrorResponse(TypedDict):
    jsonrpc: Literal["2.0"]
    id: JsonRpcRequestId | None
    error: JsonRpcErrorDetails


class JsonRpcSuccessResponse(TypedDict):
    jsonrpc: Literal["2.0"]
    id: JsonRpcRequestId
    result: Any


JsonRpcResponse: TypeAlias = JsonRpcErrorResponse | JsonRpcSuccessResponse


class JsonRpcParamDescription(TypedDict, total=False):
    name: str
    default: Any
    varargs: bool
    kwargs: bool


class JsonRpcMethodDescription(TypedDict):
    description: str | None
    params: list[JsonRpcParamDescription]


class JsonRpcWrapper:
    """
    Wrap objects and make them accessible through JSON-RPC 2.0 messaging.

    This class takes responsibility of communicating with the objects and
    processing of JSON-RPC 2.0 messages. The transport of the messages over
    HTTP, WebSocket, TCP, or whatever is of no concern to this class.

    The wrapper supports exporting the methods of one or more objects. Either
    way, the objects must be exported with method name prefixes, called
    "mounts".

    To expose objects, add them all to the objects mapping. The key in the
    mapping is used as the object's mounting point in the exposed API::

       jrw = JsonRpcWrapper(objects={
           'foo': foo,
           'hello': lambda: 'Hello, world!',
       })

    This will export the Python callables on the left as the JSON-RPC 2.0
    method names on the right::

        foo.bar() -> foo.bar
        foo.baz() -> foo.baz
        lambda    -> hello

    Only the public methods of the mounted objects, or functions/methods
    included directly in the mapping, will be exposed.

    If a method returns a :class:`pykka.Future`, the future will be completed
    and its value unwrapped before the JSON-RPC wrapper returns the response.

    For further details on the JSON-RPC 2.0 spec, see
    http://www.jsonrpc.org/specification

    :param objects: mapping between mounting points and exposed functions or
        class instances
    :type objects: dict
    :param decoders: object builders to be used by :func`json.loads`
    :type decoders: list of functions taking a dict and returning a dict
    :param encoders: object serializers to be used by :func:`json.dumps`
    :type encoders: list of :class:`json.JSONEncoder` subclasses with the
        method :meth:`default` implemented
    """

    def __init__(
        self,
        objects: dict[str, Any],
        decoders: list[Callable[[dict[Any, Any]], Any]] | None = None,
        encoders: list[type[json.JSONEncoder]] | None = None,
    ):
        if "" in objects:
            raise AttributeError("The empty string is not allowed as an object mount")
        self.objects = objects
        self.decoder = get_combined_json_decoder(decoders or [])
        self.encoder = get_combined_json_encoder(encoders or [])

    def handle_json(self, request_json: str) -> str | None:
        """
        Handles an incoming request encoded as a JSON string.

        Returns a response as a JSON string for commands, and :class:`None` for
        notifications.

        :param request_json: the serialized JSON-RPC request
        :type request_json: string
        :rtype: string or :class:`None`
        """
        try:
            request: JsonRpcRequest = json.loads(request_json, object_hook=self.decoder)
        except ValueError:
            response = JsonRpcParseError().get_response()
        else:
            response = self.handle_data(request)
        if response is None:
            return None
        return json.dumps(response, cls=self.encoder)

    def handle_data(
        self,
        request: JsonRpcRequest | list[JsonRpcRequest],
    ) -> JsonRpcResponse | list[JsonRpcResponse] | None:
        """
        Handles an incoming request in the form of a Python data structure.

        Returns a Python data structure for commands, or a :class:`None` for
        notifications.

        :param request: the unserialized JSON-RPC request
        :type request: dict
        :rtype: dict, list, or :class:`None`
        """
        if isinstance(request, list):
            return self._handle_batch(request)
        return self._handle_single_request(request)

    def _handle_batch(
        self,
        requests: list[JsonRpcRequest],
    ) -> JsonRpcErrorResponse | list[JsonRpcResponse] | None:
        if not requests:
            return JsonRpcInvalidRequestError(
                data="Batch list cannot be empty"
            ).get_response()

        responses: list[JsonRpcResponse] = []
        for request in requests:
            response = self._handle_single_request(request)
            if response:
                responses.append(response)

        return responses or None

    def _handle_single_request(self, request: JsonRpcRequest) -> JsonRpcResponse | None:
        try:
            self._validate_request(request)
            args, kwargs = self._get_params(request)
        except JsonRpcInvalidRequestError as exc:
            return exc.get_response()

        try:
            method = self._get_method(request["method"])

            try:
                result = method(*args, **kwargs)

                if "id" not in request or request["id"] is None:
                    # Request is a notification, so we don't need to respond
                    return None

                result = self._unwrap_result(result)
                return {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": result,
                }
            except TypeError as exc:
                raise JsonRpcInvalidParamsError(
                    data={
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                ) from exc
            except Exception as exc:
                raise JsonRpcApplicationError(
                    data={
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                ) from exc
        except JsonRpcError as exc:
            if "id" not in request or request["id"] is None:
                # Request is a notification, so we don't need to respond
                return None
            return exc.get_response(request["id"])

    def _validate_request(self, request: JsonRpcRequest) -> None:
        if not isinstance(request, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise JsonRpcInvalidRequestError(data="Request must be an object")
        if "jsonrpc" not in request:
            raise JsonRpcInvalidRequestError(data="'jsonrpc' member must be included")
        if request["jsonrpc"] != "2.0":
            raise JsonRpcInvalidRequestError(data="'jsonrpc' value must be '2.0'")
        if "method" not in request:
            raise JsonRpcInvalidRequestError(data="'method' member must be included")
        if not isinstance(request["method"], str):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise JsonRpcInvalidRequestError(data="'method' must be a string")

    def _get_params(self, request: JsonRpcRequest) -> tuple[list[Any], dict[Any, Any]]:
        if "params" not in request:
            return [], {}
        params = request["params"]
        if isinstance(params, list):
            return params, {}
        if isinstance(params, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            return [], params
        raise JsonRpcInvalidRequestError(
            data="'params', if given, must be an array or an object"
        )

    def _get_method(self, method_path: str) -> Callable[..., Any]:
        if callable(self.objects.get(method_path, None)):
            # The mounted object is the callable
            return self.objects[method_path]

        # The mounted object contains the callable

        if "." not in method_path:
            raise JsonRpcMethodNotFoundError(
                data=f"Could not find object mount in method name {method_path!r}"
            )

        mount, method_name = method_path.rsplit(".", 1)

        if method_name.startswith("_"):
            raise JsonRpcMethodNotFoundError(data="Private methods are not exported")

        try:
            obj = self.objects[mount]
        except KeyError as exc:
            raise JsonRpcMethodNotFoundError(
                data=f"No object found at {mount!r}"
            ) from exc

        try:
            return getattr(obj, method_name)
        except AttributeError as exc:
            raise JsonRpcMethodNotFoundError(
                data=f"Object mounted at {mount!r} has no member {method_name!r}"
            ) from exc

    def _unwrap_result(self, result: pykka.Future[T] | T) -> T:
        if isinstance(result, pykka.Future):
            return result.get()  # pyright: ignore[reportUnknownVariableType]
        return result


class JsonRpcError(Exception):
    code = -32000
    message = "Unspecified server error"

    def __init__(self, data: Any | None = None) -> None:
        self.data = data

    def get_response(
        self,
        request_id: JsonRpcRequestId | None = None,
    ) -> JsonRpcErrorResponse:
        response: JsonRpcErrorResponse = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": self.code, "message": self.message},
        }
        if self.data:
            response["error"]["data"] = self.data
        return response


class JsonRpcParseError(JsonRpcError):
    code = -32700
    message = "Parse error"


class JsonRpcInvalidRequestError(JsonRpcError):
    code = -32600
    message = "Invalid Request"


class JsonRpcMethodNotFoundError(JsonRpcError):
    code = -32601
    message = "Method not found"


class JsonRpcInvalidParamsError(JsonRpcError):
    code = -32602
    message = "Invalid params"


class JsonRpcApplicationError(JsonRpcError):
    code = 0
    message = "Application error"


def get_combined_json_decoder(
    decoders: list[Callable[[dict[Any, Any]], Any]],
) -> Callable[[dict[Any, Any]], Any]:
    def decode(dct: dict[Any, Any]) -> dict[Any, Any]:
        for decoder in decoders:
            dct = decoder(dct)
        return dct

    return decode


def get_combined_json_encoder(
    encoders: list[type[json.JSONEncoder]],
) -> type[json.JSONEncoder]:
    class JsonRpcEncoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            for encoder in encoders:
                try:
                    return encoder().default(o)
                except TypeError:
                    pass  # Try next encoder
            return json.JSONEncoder.default(self, o)

    return JsonRpcEncoder


class JsonRpcInspector:
    """
    Inspects a group of classes and functions to create a description of what
    methods they can expose over JSON-RPC 2.0.

    To inspect one or more classes, add them all to the objects mapping. The
    key in the mapping is used as the classes' mounting point in the exposed
    API::

        jri = JsonRpcInspector(objects={
            'foo': Foo,
            'hello': lambda: 'Hello, world!',
        })

    Since the inspector is based on inspecting classes and not instances, it
    will not include methods added dynamically. The wrapper works with
    instances, and it will thus export dynamically added methods as well.

    :param objects: mapping between mounts and exposed functions or classes
    :type objects: dict
    """

    def __init__(self, objects: dict[str, Callable[..., Any]]) -> None:
        if "" in objects:
            raise AttributeError("The empty string is not allowed as an object mount")
        self.objects = objects

    def describe(self) -> dict[str, Any]:
        """
        Inspects the object and returns a data structure which describes the
        available properties and methods.
        """
        methods: dict[str, JsonRpcMethodDescription] = {}
        for mount, obj in self.objects.items():
            if inspect.isroutine(obj):
                methods[mount] = self._describe_method(obj)
            else:
                obj_methods = self._get_methods(obj)
                for name, description in obj_methods.items():
                    if mount:
                        name = f"{mount}.{name}"
                    methods[name] = description
        return methods

    def _get_methods(self, obj: Any) -> dict[str, JsonRpcMethodDescription]:
        methods: dict[str, JsonRpcMethodDescription] = {}
        for name, value in inspect.getmembers(obj):
            if name.startswith("_"):
                continue
            if not inspect.isroutine(value):
                continue
            method = self._describe_method(value)
            if method:
                methods[name] = method
        return methods

    def _describe_method(self, method: Callable[..., Any]) -> JsonRpcMethodDescription:
        return {
            "description": inspect.getdoc(method),
            "params": self._describe_params(method),
        }

    def _describe_params(
        self,
        method: Callable[..., Any],
    ) -> list[JsonRpcParamDescription]:
        argspec = inspect.getfullargspec(method)

        defaults = list(argspec.defaults) if argspec.defaults else []
        num_args_without_default = len(argspec.args) - len(defaults)
        no_defaults = [None] * num_args_without_default
        defaults = no_defaults + defaults

        params: list[JsonRpcParamDescription] = []

        for arg, _default in zip(argspec.args, defaults, strict=True):
            if arg == "self":
                continue
            params.append({"name": arg})

        if argspec.defaults:
            for i, default in enumerate(reversed(argspec.defaults)):
                params[len(params) - i - 1]["default"] = default

        if argspec.varargs:
            params.append({"name": argspec.varargs, "varargs": True})

        if argspec.varkw:
            params.append({"name": argspec.varkw, "kwargs": True})

        return params
