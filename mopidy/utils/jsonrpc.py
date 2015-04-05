from __future__ import absolute_import, unicode_literals

import inspect
import json
import traceback

import pykka

from mopidy import compat


class JsonRpcWrapper(object):

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

    def __init__(self, objects, decoders=None, encoders=None):
        if '' in objects.keys():
            raise AttributeError(
                'The empty string is not allowed as an object mount')
        self.objects = objects
        self.decoder = get_combined_json_decoder(decoders or [])
        self.encoder = get_combined_json_encoder(encoders or [])

    def handle_json(self, request):
        """
        Handles an incoming request encoded as a JSON string.

        Returns a response as a JSON string for commands, and :class:`None` for
        notifications.

        :param request: the serialized JSON-RPC request
        :type request: string
        :rtype: string or :class:`None`
        """
        try:
            request = json.loads(request, object_hook=self.decoder)
        except ValueError:
            response = JsonRpcParseError().get_response()
        else:
            response = self.handle_data(request)
        if response is None:
            return None
        return json.dumps(response, cls=self.encoder)

    def handle_data(self, request):
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
        else:
            return self._handle_single_request(request)

    def _handle_batch(self, requests):
        if not requests:
            return JsonRpcInvalidRequestError(
                data='Batch list cannot be empty').get_response()

        responses = []
        for request in requests:
            response = self._handle_single_request(request)
            if response:
                responses.append(response)

        return responses or None

    def _handle_single_request(self, request):
        try:
            self._validate_request(request)
            args, kwargs = self._get_params(request)
        except JsonRpcInvalidRequestError as error:
            return error.get_response()

        try:
            method = self._get_method(request['method'])

            try:
                result = method(*args, **kwargs)

                if self._is_notification(request):
                    return None

                result = self._unwrap_result(result)

                return {
                    'jsonrpc': '2.0',
                    'id': request['id'],
                    'result': result,
                }
            except TypeError as error:
                raise JsonRpcInvalidParamsError(data={
                    'type': error.__class__.__name__,
                    'message': compat.text_type(error),
                    'traceback': traceback.format_exc(),
                })
            except Exception as error:
                raise JsonRpcApplicationError(data={
                    'type': error.__class__.__name__,
                    'message': compat.text_type(error),
                    'traceback': traceback.format_exc(),
                })
        except JsonRpcError as error:
            if self._is_notification(request):
                return None
            return error.get_response(request['id'])

    def _validate_request(self, request):
        if not isinstance(request, dict):
            raise JsonRpcInvalidRequestError(
                data='Request must be an object')
        if 'jsonrpc' not in request:
            raise JsonRpcInvalidRequestError(
                data='"jsonrpc" member must be included')
        if request['jsonrpc'] != '2.0':
            raise JsonRpcInvalidRequestError(
                data='"jsonrpc" value must be "2.0"')
        if 'method' not in request:
            raise JsonRpcInvalidRequestError(
                data='"method" member must be included')
        if not isinstance(request['method'], compat.text_type):
            raise JsonRpcInvalidRequestError(
                data='"method" must be a string')

    def _get_params(self, request):
        if 'params' not in request:
            return [], {}
        params = request['params']
        if isinstance(params, list):
            return params, {}
        elif isinstance(params, dict):
            return [], params
        else:
            raise JsonRpcInvalidRequestError(
                data='"params", if given, must be an array or an object')

    def _get_method(self, method_path):
        if callable(self.objects.get(method_path, None)):
            # The mounted object is the callable
            return self.objects[method_path]

        # The mounted object contains the callable

        if '.' not in method_path:
            raise JsonRpcMethodNotFoundError(
                data='Could not find object mount in method name "%s"' % (
                    method_path))

        mount, method_name = method_path.rsplit('.', 1)

        if method_name.startswith('_'):
            raise JsonRpcMethodNotFoundError(
                data='Private methods are not exported')

        try:
            obj = self.objects[mount]
        except KeyError:
            raise JsonRpcMethodNotFoundError(
                data='No object found at "%s"' % mount)

        try:
            return getattr(obj, method_name)
        except AttributeError:
            raise JsonRpcMethodNotFoundError(
                data='Object mounted at "%s" has no member "%s"' % (
                    mount, method_name))

    def _is_notification(self, request):
        return 'id' not in request

    def _unwrap_result(self, result):
        if isinstance(result, pykka.Future):
            result = result.get()
        return result


class JsonRpcError(Exception):
    code = -32000
    message = 'Unspecified server error'

    def __init__(self, data=None):
        self.data = data

    def get_response(self, request_id=None):
        response = {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': self.code,
                'message': self.message,
            },
        }
        if self.data:
            response['error']['data'] = self.data
        return response


class JsonRpcParseError(JsonRpcError):
    code = -32700
    message = 'Parse error'


class JsonRpcInvalidRequestError(JsonRpcError):
    code = -32600
    message = 'Invalid Request'


class JsonRpcMethodNotFoundError(JsonRpcError):
    code = -32601
    message = 'Method not found'


class JsonRpcInvalidParamsError(JsonRpcError):
    code = -32602
    message = 'Invalid params'


class JsonRpcApplicationError(JsonRpcError):
    code = 0
    message = 'Application error'


def get_combined_json_decoder(decoders):
    def decode(dct):
        for decoder in decoders:
            dct = decoder(dct)
        return dct
    return decode


def get_combined_json_encoder(encoders):
    class JsonRpcEncoder(json.JSONEncoder):

        def default(self, obj):
            for encoder in encoders:
                try:
                    return encoder().default(obj)
                except TypeError:
                    pass  # Try next encoder
            return json.JSONEncoder.default(self, obj)
    return JsonRpcEncoder


class JsonRpcInspector(object):

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

    def __init__(self, objects):
        if '' in objects.keys():
            raise AttributeError(
                'The empty string is not allowed as an object mount')
        self.objects = objects

    def describe(self):
        """
        Inspects the object and returns a data structure which describes the
        available properties and methods.
        """
        methods = {}
        for mount, obj in self.objects.items():
            if inspect.isroutine(obj):
                methods[mount] = self._describe_method(obj)
            else:
                obj_methods = self._get_methods(obj)
                for name, description in obj_methods.items():
                    if mount:
                        name = '%s.%s' % (mount, name)
                    methods[name] = description
        return methods

    def _get_methods(self, obj):
        methods = {}
        for name, value in inspect.getmembers(obj):
            if name.startswith('_'):
                continue
            if not inspect.isroutine(value):
                continue
            method = self._describe_method(value)
            if method:
                methods[name] = method
        return methods

    def _describe_method(self, method):
        return {
            'description': inspect.getdoc(method),
            'params': self._describe_params(method),
        }

    def _describe_params(self, method):
        argspec = inspect.getargspec(method)

        defaults = argspec.defaults and list(argspec.defaults) or []
        num_args_without_default = len(argspec.args) - len(defaults)
        no_defaults = [None] * num_args_without_default
        defaults = no_defaults + defaults

        params = []

        for arg, default in zip(argspec.args, defaults):
            if arg == 'self':
                continue
            params.append({'name': arg})

        if argspec.defaults:
            for i, default in enumerate(reversed(argspec.defaults)):
                params[len(params) - i - 1]['default'] = default

        if argspec.varargs:
            params.append({
                'name': argspec.varargs,
                'varargs': True,
            })

        if argspec.keywords:
            params.append({
                'name': argspec.keywords,
                'kwargs': True,
            })

        return params
