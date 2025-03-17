import inspect
import traceback
from collections.abc import Callable
from typing import Any, Literal, TypeAlias, TypeVar

import pydantic_core
import pykka
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    TypeAdapter,
    field_serializer,
    model_serializer,
)
from pydantic_core import PydanticUndefined, PydanticUndefinedType

from mopidy import models

T = TypeVar("T")


class UnsetType:
    pass


Unset = UnsetType()


RequestId: TypeAlias = str | int | float
Param: TypeAlias = (
    # The complex types we support in the core API:
    models.Artist
    | models.Album
    | models.Track
    | models.Playlist
    | models.Ref
    | models.Image
    # This covers any primitive JSON types:
    | Any
)


class Request(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: RequestId | None = None
    method: str
    params: list[Param] | dict[str, Param] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", frozen=True)


RequestTypeAdapter = TypeAdapter(Request | list[Request])
RequestDict: TypeAlias = dict[str, Any]


class ErrorDetails(BaseModel):
    code: int
    message: str
    data: Any | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)


class ErrorResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: RequestId | None
    error: ErrorDetails

    model_config = ConfigDict(extra="forbid", frozen=True)


class SuccessResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: RequestId
    result: Any

    model_config = ConfigDict(extra="forbid", frozen=True)


Response: TypeAlias = SuccessResponse | ErrorResponse
ResponseTypeAdapter = TypeAdapter(Response | list[Response])


class ParamDescription(BaseModel):
    name: str
    default: Any = Unset
    varargs: Any = Unset
    kwargs: Any = Unset

    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_serializer("default", when_used="json")
    def serialize_default(self, _nxt: SerializerFunctionWrapHandler):
        return None if self.default is Unset else self.default

    @field_serializer("varargs", when_used="json")
    def serialize_varargs(self, _nxt: SerializerFunctionWrapHandler):
        return None if self.varargs is Unset else self.varargs

    @field_serializer("kwargs", when_used="json")
    def serialize_kwargs(self, _nxt: SerializerFunctionWrapHandler):
        return None if self.kwargs is Unset else self.kwargs

    @model_serializer(mode="wrap", when_used="json")
    def serialize_model(self, nxt: SerializerFunctionWrapHandler):
        serialized = nxt(self)
        if self.default is Unset:
            del serialized["default"]
        if self.varargs is Unset:
            del serialized["varargs"]
        if self.kwargs is Unset:
            del serialized["kwargs"]
        return serialized


class MethodDescription(BaseModel):
    description: str | None
    params: list[ParamDescription]

    model_config = ConfigDict(extra="forbid", frozen=True)


class Wrapper:
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
    https://www.jsonrpc.org/specification

    :param objects: mapping between mounting points and exposed functions or
        class instances
    :type objects: dict
    """

    def __init__(
        self,
        objects: dict[str, Any],
    ):
        if "" in objects:
            msg = "The empty string is not allowed as an object mount"
            raise AttributeError(msg)
        self.objects = objects

    def handle_json(self, request_json: str | bytes) -> bytes | None:
        """
        Handles an incoming request encoded as a JSON string.

        Returns a response as a JSON string for commands, and :class:`None` for
        notifications.

        :param request_json: the serialized JSON-RPC request
        :type request_json: string
        :rtype: string or :class:`None`
        """
        try:
            request = pydantic_core.from_json(request_json)
        except ValueError:
            response = ParseError().get_response()
        else:
            response = self.handle_data(request)
        if response is None:
            return None
        return ResponseTypeAdapter.dump_json(response, by_alias=True)

    def handle_data(
        self,
        request: RequestDict | list[RequestDict],
    ) -> Response | list[Response] | None:
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
        requests: list[RequestDict],
    ) -> Response | list[Response] | None:
        if not requests:
            return InvalidRequestError(
                data="Batch list cannot be empty",
            ).get_response()

        responses: list[Response] = []
        for request in requests:
            response = self._handle_single_request(request)
            if response:
                responses.append(response)

        return responses or None

    def _handle_single_request(self, request_dict: RequestDict) -> Response | None:
        try:
            request = self._validate_request(request_dict)
        except InvalidRequestError as exc:
            return exc.get_response()
        else:
            args, kwargs = self._get_params(request)

        try:
            method = self._get_method(request.method)

            try:
                result = method(*args, **kwargs)

                if request.id is None:
                    # Request is a notification, so we don't need to respond
                    return None

                result = self._unwrap_result(result)
                return SuccessResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    result=result,
                )
            except TypeError as exc:
                raise InvalidParamsError(
                    data={
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                ) from exc
            except Exception as exc:
                raise ApplicationError(
                    data={
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                ) from exc
        except JsonRpcError as exc:
            if request.id is None:
                # Request is a notification, so we don't need to respond
                return None
            return exc.get_response(request.id)

    def _validate_request(self, request_dict: RequestDict) -> Request:
        if not isinstance(request_dict, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise InvalidRequestError(data="Request must be an object")
        if "jsonrpc" not in request_dict:
            raise InvalidRequestError(data="'jsonrpc' member must be included")
        if request_dict["jsonrpc"] != "2.0":
            raise InvalidRequestError(data="'jsonrpc' value must be '2.0'")
        if "method" not in request_dict:
            raise InvalidRequestError(data="'method' member must be included")
        if not isinstance(request_dict["method"], str):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise InvalidRequestError(data="'method' must be a string")
        if "params" in request_dict and not isinstance(
            request_dict["params"], list | dict
        ):
            raise InvalidRequestError(
                data="'params', if given, must be an array or an object",
            )
        return Request.model_validate(request_dict)

    def _get_params(self, request: Request) -> tuple[list[Any], dict[Any, Any]]:
        match request.params:
            case list():
                return request.params, {}
            case dict():
                return [], request.params

    def _get_method(self, method_path: str) -> Callable[..., Any]:
        if callable(self.objects.get(method_path, None)):
            # The mounted object is the callable
            return self.objects[method_path]

        # The mounted object contains the callable

        if "." not in method_path:
            raise MethodNotFoundError(
                data=f"Could not find object mount in method name {method_path!r}",
            )

        mount, method_name = method_path.rsplit(".", 1)

        if method_name.startswith("_"):
            raise MethodNotFoundError(data="Private methods are not exported")

        try:
            obj = self.objects[mount]
        except KeyError as exc:
            raise MethodNotFoundError(
                data=f"No object found at {mount!r}",
            ) from exc

        try:
            return getattr(obj, method_name)
        except AttributeError as exc:
            raise MethodNotFoundError(
                data=f"Object mounted at {mount!r} has no member {method_name!r}",
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
        request_id: RequestId | None = None,
    ) -> ErrorResponse:
        return ErrorResponse(
            jsonrpc="2.0",
            id=request_id,
            error=ErrorDetails(
                code=self.code,
                message=self.message,
                data=self.data,
            ),
        )


class ParseError(JsonRpcError):
    code = -32700
    message = "Parse error"


class InvalidRequestError(JsonRpcError):
    code = -32600
    message = "Invalid Request"


class MethodNotFoundError(JsonRpcError):
    code = -32601
    message = "Method not found"


class InvalidParamsError(JsonRpcError):
    code = -32602
    message = "Invalid params"


class ApplicationError(JsonRpcError):
    code = 0
    message = "Application error"


class Inspector:
    """
    Inspects a group of classes and functions to create a description of what
    methods they can expose over JSON-RPC 2.0.

    To inspect one or more classes, add them all to the objects mapping. The
    key in the mapping is used as the classes' mounting point in the exposed
    API::

        inspector = Inspector(objects={
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
            msg = "The empty string is not allowed as an object mount"
            raise AttributeError(msg)
        self.objects = objects

    def describe(self) -> dict[str, MethodDescription]:
        """
        Inspects the object and returns a data structure which describes the
        available properties and methods.
        """
        methods: dict[str, MethodDescription] = {}
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

    def _get_methods(self, obj: Any) -> dict[str, MethodDescription]:
        methods: dict[str, MethodDescription] = {}
        for name, value in inspect.getmembers(obj):
            if name.startswith("_"):
                continue
            if not inspect.isroutine(value):
                continue
            method = self._describe_method(value)
            if method:
                methods[name] = method
        return methods

    def _describe_method(self, method: Callable[..., Any]) -> MethodDescription:
        return MethodDescription(
            description=inspect.getdoc(method),
            params=self._describe_params(method),
        )

    def _describe_params(
        self,
        method: Callable[..., Any],
    ) -> list[ParamDescription]:
        argspec = inspect.getfullargspec(method)

        with_defaults: list[Any] = list(argspec.defaults) if argspec.defaults else []
        num_args_without_default = len(argspec.args) - len(with_defaults)
        without_defaults: list[PydanticUndefinedType] = [
            PydanticUndefined
        ] * num_args_without_default
        defaults = without_defaults + with_defaults

        params: list[ParamDescription] = []

        for arg, default in zip(argspec.args, defaults, strict=True):
            if arg == "self":
                continue
            params.append(ParamDescription(name=arg, default=default))

        if argspec.varargs:
            params.append(ParamDescription(name=argspec.varargs, varargs=True))

        if argspec.varkw:
            params.append(ParamDescription(name=argspec.varkw, kwargs=True))

        return params
