from __future__ import unicode_literals

import json
import traceback

import pykka


class JsonRpcWrapper(object):
    """
    Wraps objects and make them accessible through JSON-RPC 2.0 messaging.

    This class takes responsibility of communicating with the objects and
    processing of JSON-RPC 2.0 messages. The transport of the messages over
    HTTP, WebSocket, TCP, or whatever is of no concern to this class.

    The objects can either be Pykka actors or plain objects. Only their public
    methods will be exposed, not any attributes.

    If a method returns an object with a ``get()`` method, it is assumed to be
    a future object. Any futures is completed and their value unwrapped before
    the JSON RPC wrapper returns the response.

    For further details on the JSON-RPC 2.0 spec, see
    http://www.jsonrpc.org/specification

    :param objects: dict of names mapped to objects to be exposed
    """

    def __init__(self, objects, decoders=None, encoders=None):
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

                if self._is_future(result):
                    result = result.get()

                return {
                    'jsonrpc': '2.0',
                    'id': request['id'],
                    'result': result,
                }
            except TypeError as error:
                raise JsonRpcInvalidParamsError(data={
                    'type': error.__class__.__name__,
                    'message': unicode(error),
                    'traceback': traceback.format_exc(),
                })
            except Exception as error:
                raise JsonRpcApplicationError(data={
                    'type': error.__class__.__name__,
                    'message': unicode(error),
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
        if not 'jsonrpc' in request:
            raise JsonRpcInvalidRequestError(
                data='"jsonrpc" member must be included')
        if request['jsonrpc'] != '2.0':
            raise JsonRpcInvalidRequestError(
                data='"jsonrpc" value must be "2.0"')
        if not 'method' in request:
            raise JsonRpcInvalidRequestError(
                data='"method" member must be included')
        if not isinstance(request['method'], unicode):
            raise JsonRpcInvalidRequestError(
                data='"method" must be a string')

    def _get_params(self, request):
        if not 'params' in request:
            return [], {}
        params = request['params']
        if isinstance(params, list):
            return params, {}
        elif isinstance(params, dict):
            return [], params
        else:
            raise JsonRpcInvalidRequestError(
                data='"params", if given, must be an array or an object')

    def _get_method(self, name):
        try:
            path = name.split('.')
            root = path.pop(0)
            this = self.objects[root]
            for part in path:
                if part.startswith('_'):
                    raise AttributeError
                this = getattr(this, part)
            return this
        except (AttributeError, KeyError):
            raise JsonRpcMethodNotFoundError()

    def _is_notification(self, request):
        return 'id' not in request

    def _is_future(self, result):
        return isinstance(result, pykka.Future)


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
