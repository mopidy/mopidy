import inspect
import traceback
from collections.abc import Callable
from typing import Any, Literal, Self, TypeAlias, TypeVar

import msgspec
import pykka

from mopidy import models

T = TypeVar("T")

RequestId: TypeAlias = str | int | float
Model: TypeAlias = (
    models.Album
    | models.Artist
    | models.Image
    | models.Playlist
    | models.Ref
    | models.SearchResult
    | models.TlTrack
    | models.Track
)
ParamValue: TypeAlias = None | bool | int | float | str | Model
Param: TypeAlias = ParamValue | list[ParamValue]


class Request(msgspec.Struct, kw_only=True, omit_defaults=True):
    jsonrpc: Literal["2.0"]
    method: str
    params: list[Param] | dict[str, Param] | None = None
    id: RequestId | None = None

    @classmethod
    def build(
        cls,
        method: str,
        params: list[Param] | dict[str, Param] | None = None,
        id: RequestId | None = None,
    ) -> Self:
        return cls(jsonrpc="2.0", method=method, params=params, id=id)


class ErrorResponseDetails(msgspec.Struct, kw_only=True, omit_defaults=True):
    code: int
    message: str
    data: Any | None = None


class Response(msgspec.Struct, kw_only=True, omit_defaults=True):
    jsonrpc: Literal["2.0"]
    id: RequestId | None  # None is allowed, but it must be set explicitly.
    result: Any | msgspec.UnsetType = msgspec.UNSET
    error: ErrorResponseDetails | None | msgspec.UnsetType = msgspec.UNSET

    @classmethod
    def as_success(cls, id: RequestId, result: Any) -> Self:
        return cls(jsonrpc="2.0", id=id, result=result)

    @classmethod
    def as_error(cls, id: RequestId | None, error: ErrorResponseDetails) -> Self:
        return cls(jsonrpc="2.0", id=id, error=error)


class ParamDescription(msgspec.Struct, kw_only=True, omit_defaults=True):
    name: str
    default: Any | None = None
    varargs: bool | None = None
    kwargs: bool | None = None


class MethodDescription(msgspec.Struct, kw_only=True):
    description: str | None
    params: list[ParamDescription]


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
    ) -> None:
        if "" in objects:
            msg = "The empty string is not allowed as an object mount"
            raise AttributeError(msg)
        self.objects = objects

    def handle_json(self, request_json: str) -> bytes | None:
        """
        Handles an incoming request encoded as a JSON string.

        Returns a response as a JSON string for commands, and :class:`None` for
        notifications.

        :param request_json: the serialized JSON-RPC request
        :type request_json: string
        :rtype: string or :class:`None`
        """
        try:
            request = msgspec.json.decode(
                request_json,
                type=Request | list[Request],
            )
        except msgspec.ValidationError as exc:
            response = InvalidRequestError(data=str(exc)).get_response()
        except msgspec.DecodeError:
            response = ParseError().get_response()
        else:
            response = self.handle_data(request)
        if response is None:
            return None
        return msgspec.json.encode(response)

    def handle_data(
        self,
        request: Request | list[Request],
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
        requests: list[Request],
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

    def _handle_single_request(self, request: Request) -> Response | None:
        try:
            args, kwargs = self._get_params(request)
        except InvalidRequestError as exc:
            return exc.get_response()

        try:
            method = self._get_method(request.method)

            try:
                result = method(*args, **kwargs)

                if request.id is None:
                    # Request is a notification, so we don't need to respond
                    return None

                result = self._unwrap_result(result)
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
            else:
                return Response.as_success(id=request.id, result=result)
        except JsonRpcError as exc:
            if request.id is None:
                # Request is a notification, so we don't need to respond
                return None
            return exc.get_response(request.id)

    def _get_params(self, request: Request) -> tuple[list[Any], dict[Any, Any]]:
        if request.params is None:
            return [], {}
        params = request.params
        if isinstance(params, list):
            return params, {}
        if isinstance(params, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            return [], params
        raise InvalidRequestError(
            data="'params', if given, must be an array or an object",
        )

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
    ) -> Response:
        return Response.as_error(
            id=request_id,
            error=ErrorResponseDetails(
                code=self.code,
                message=self.message,
                data=self.data if self.data else None,
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

        defaults = list(argspec.defaults) if argspec.defaults else []
        num_args_without_default = len(argspec.args) - len(defaults)
        no_defaults = [None] * num_args_without_default
        defaults = no_defaults + defaults

        params: list[ParamDescription] = []

        for arg, _default in zip(argspec.args, defaults, strict=True):
            if arg == "self":
                continue
            params.append(ParamDescription(name=arg))

        if argspec.defaults:
            for i, default in enumerate(reversed(argspec.defaults)):
                params[len(params) - i - 1].default = default

        if argspec.varargs:
            params.append(ParamDescription(name=argspec.varargs, varargs=True))

        if argspec.varkw:
            params.append(ParamDescription(name=argspec.varkw, kwargs=True))

        return params
