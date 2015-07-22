from __future__ import absolute_import, unicode_literals

import json
import unittest

import mock

import pykka

from mopidy import core, models
from mopidy.internal import deprecation, jsonrpc

from tests import dummy_backend


class Calculator(object):

    def __init__(self):
        self._mem = None

    def model(self):
        return 'TI83'

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
            'add': 'Returns the sum of the terms',
            'sub': 'Returns the diff of the terms',
        }

    def take_it_all(self, a, b, c=True, *args, **kwargs):
        pass

    def _secret(self):
        return 'Grand Unified Theory'

    def fail(self):
        raise ValueError('What did you expect?')


class JsonRpcTestBase(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.backend = dummy_backend.create_proxy()
        self.calc = Calculator()

        with deprecation.ignore():
            self.core = core.Core.start(backends=[self.backend]).proxy()

        self.jrw = jsonrpc.JsonRpcWrapper(
            objects={
                'hello': lambda: 'Hello, world!',
                'calc': self.calc,
                'core': self.core,
                'core.playback': self.core.playback,
                'core.tracklist': self.core.tracklist,
                'get_uri_schemes': self.core.get_uri_schemes,
            },
            encoders=[models.ModelJSONEncoder],
            decoders=[models.model_json_decoder])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()


class JsonRpcSetupTest(JsonRpcTestBase):

    def test_empty_object_mounts_is_not_allowed(self):
        with self.assertRaises(AttributeError):
            jsonrpc.JsonRpcWrapper(objects={'': Calculator()})


class JsonRpcSerializationTest(JsonRpcTestBase):

    def test_handle_json_converts_from_and_to_json(self):
        self.jrw.handle_data = mock.Mock()
        self.jrw.handle_data.return_value = {'foo': 'response'}

        request = '{"foo": "request"}'
        response = self.jrw.handle_json(request)

        self.jrw.handle_data.assert_called_once_with({'foo': 'request'})
        self.assertEqual(response, '{"foo": "response"}')

    def test_handle_json_decodes_mopidy_models(self):
        self.jrw.handle_data = mock.Mock()
        self.jrw.handle_data.return_value = []

        request = '{"foo": {"__model__": "Artist", "name": "bar"}}'
        self.jrw.handle_json(request)

        self.jrw.handle_data.assert_called_once_with(
            {'foo': models.Artist(name='bar')})

    def test_handle_json_encodes_mopidy_models(self):
        self.jrw.handle_data = mock.Mock()
        self.jrw.handle_data.return_value = {'foo': models.Artist(name='bar')}

        request = '[]'
        response = json.loads(self.jrw.handle_json(request))

        self.assertIn('foo', response)
        self.assertIn('__model__', response['foo'])
        self.assertEqual(response['foo']['__model__'], 'Artist')
        self.assertIn('name', response['foo'])
        self.assertEqual(response['foo']['name'], 'bar')

    def test_handle_json_returns_nothing_for_notices(self):
        request = '{"jsonrpc": "2.0", "method": "core.get_uri_schemes"}'
        response = self.jrw.handle_json(request)

        self.assertEqual(response, None)

    def test_invalid_json_command_causes_parse_error(self):
        request = (
            '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]')
        response = self.jrw.handle_json(request)
        response = json.loads(response)

        self.assertEqual(response['jsonrpc'], '2.0')
        error = response['error']
        self.assertEqual(error['code'], -32700)
        self.assertEqual(error['message'], 'Parse error')

    def test_invalid_json_batch_causes_parse_error(self):
        request = """[
            {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},
            {"jsonrpc": "2.0", "method"
        ]"""
        response = self.jrw.handle_json(request)
        response = json.loads(response)

        self.assertEqual(response['jsonrpc'], '2.0')
        error = response['error']
        self.assertEqual(error['code'], -32700)
        self.assertEqual(error['message'], 'Parse error')


class JsonRpcSingleCommandTest(JsonRpcTestBase):

    def test_call_method_on_root(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'hello',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], 1)
        self.assertNotIn('error', response)
        self.assertEqual(response['result'], 'Hello, world!')

    def test_call_method_on_plain_object(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calc.model',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], 1)
        self.assertNotIn('error', response)
        self.assertEqual(response['result'], 'TI83')

    def test_call_method_which_returns_dict_from_plain_object(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calc.describe',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], 1)
        self.assertNotIn('error', response)
        self.assertIn('add', response['result'])
        self.assertIn('sub', response['result'])

    def test_call_method_on_actor_root(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.get_uri_schemes',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], 1)
        self.assertNotIn('error', response)
        self.assertEqual(response['result'], ['dummy'])

    def test_call_method_on_actor_member(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.playback.get_time_position',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['result'], 0)

    def test_call_method_which_is_a_directly_mounted_actor_member(self):
        # 'get_uri_schemes' isn't a regular callable, but a Pykka
        # CallableProxy. This test checks that CallableProxy objects are
        # threated by JsonRpcWrapper like any other callable.

        request = {
            'jsonrpc': '2.0',
            'method': 'get_uri_schemes',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['jsonrpc'], '2.0')
        self.assertEqual(response['id'], 1)
        self.assertNotIn('error', response)
        self.assertEqual(response['result'], ['dummy'])

    def test_call_method_with_positional_params(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calc.add',
            'params': [3, 4],
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['result'], 7)

    def test_call_methods_with_named_params(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calc.add',
            'params': {'a': 3, 'b': 4},
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['result'], 7)


class JsonRpcSingleNotificationTest(JsonRpcTestBase):

    def test_notification_does_not_return_a_result(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.get_uri_schemes',
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)

    def test_notification_makes_an_observable_change(self):
        self.assertEqual(self.calc.get_mem(), None)

        request = {
            'jsonrpc': '2.0',
            'method': 'calc.set_mem',
            'params': [37],
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)
        self.assertEqual(self.calc.get_mem(), 37)

    def test_notification_unknown_method_returns_nothing(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'bogus',
            'params': ['bogus'],
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)


class JsonRpcBatchTest(JsonRpcTestBase):

    def test_batch_of_only_commands_returns_all(self):
        self.core.tracklist.set_random(True).get()

        request = [
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_repeat', 'id': 1},
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_random', 'id': 2},
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_single', 'id': 3},
        ]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 3)

        response = dict((row['id'], row) for row in response)
        self.assertEqual(response[1]['result'], False)
        self.assertEqual(response[2]['result'], True)
        self.assertEqual(response[3]['result'], False)

    def test_batch_of_commands_and_notifications_returns_some(self):
        self.core.tracklist.set_random(True).get()

        request = [
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_repeat'},
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_random', 'id': 2},
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_single', 'id': 3},
        ]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 2)

        response = dict((row['id'], row) for row in response)
        self.assertNotIn(1, response)
        self.assertEqual(response[2]['result'], True)
        self.assertEqual(response[3]['result'], False)

    def test_batch_of_only_notifications_returns_nothing(self):
        self.core.tracklist.set_random(True).get()

        request = [
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_repeat'},
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_random'},
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_single'},
        ]
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)


class JsonRpcSingleCommandErrorTest(JsonRpcTestBase):

    def test_application_error_response(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calc.fail',
            'params': [],
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertNotIn('result', response)

        error = response['error']
        self.assertEqual(error['code'], 0)
        self.assertEqual(error['message'], 'Application error')

        data = error['data']
        self.assertEqual(data['type'], 'ValueError')
        self.assertIn('What did you expect?', data['message'])
        self.assertIn('traceback', data)
        self.assertIn('Traceback (most recent call last):', data['traceback'])

    def test_missing_jsonrpc_member_causes_invalid_request_error(self):
        request = {
            'method': 'core.get_uri_schemes',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], '"jsonrpc" member must be included')

    def test_wrong_jsonrpc_version_causes_invalid_request_error(self):
        request = {
            'jsonrpc': '3.0',
            'method': 'core.get_uri_schemes',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], '"jsonrpc" value must be "2.0"')

    def test_missing_method_member_causes_invalid_request_error(self):
        request = {
            'jsonrpc': '2.0',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], '"method" member must be included')

    def test_invalid_method_value_causes_invalid_request_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 1,
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], '"method" must be a string')

    def test_invalid_params_value_causes_invalid_request_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.get_uri_schemes',
            'params': 'foobar',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(
            error['data'], '"params", if given, must be an array or an object')

    def test_method_on_without_object_causes_unknown_method_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'bogus',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32601)
        self.assertEqual(error['message'], 'Method not found')
        self.assertEqual(
            error['data'],
            'Could not find object mount in method name "bogus"')

    def test_method_on_unknown_object_causes_unknown_method_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'bogus.bogus',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32601)
        self.assertEqual(error['message'], 'Method not found')
        self.assertEqual(error['data'], 'No object found at "bogus"')

    def test_unknown_method_on_known_object_causes_unknown_method_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.bogus',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32601)
        self.assertEqual(error['message'], 'Method not found')
        self.assertEqual(
            error['data'], 'Object mounted at "core" has no member "bogus"')

    def test_private_method_causes_unknown_method_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core._secret',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32601)
        self.assertEqual(error['message'], 'Method not found')
        self.assertEqual(error['data'], 'Private methods are not exported')

    def test_invalid_params_causes_invalid_params_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.get_uri_schemes',
            'params': ['bogus'],
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32602)
        self.assertEqual(error['message'], 'Invalid params')

        data = error['data']
        self.assertEqual(data['type'], 'TypeError')
        self.assertEqual(
            data['message'],
            'get_uri_schemes() takes exactly 1 argument (2 given)')
        self.assertIn('traceback', data)
        self.assertIn('Traceback (most recent call last):', data['traceback'])


class JsonRpcBatchErrorTest(JsonRpcTestBase):

    def test_empty_batch_list_causes_invalid_request_error(self):
        request = []
        response = self.jrw.handle_data(request)

        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], 'Batch list cannot be empty')

    def test_batch_with_invalid_command_causes_invalid_request_error(self):
        request = [1]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 1)
        response = response[0]
        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], 'Request must be an object')

    def test_batch_with_invalid_commands_causes_invalid_request_error(self):
        request = [1, 2, 3]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 3)
        response = response[2]
        self.assertIsNone(response['id'])
        error = response['error']
        self.assertEqual(error['code'], -32600)
        self.assertEqual(error['message'], 'Invalid Request')
        self.assertEqual(error['data'], 'Request must be an object')

    def test_batch_of_both_successfull_and_failing_requests(self):
        request = [
            # Call with positional params
            {'jsonrpc': '2.0', 'method': 'core.playback.seek',
                'params': [47], 'id': '1'},
            # Notification
            {'jsonrpc': '2.0', 'method': 'core.tracklist.set_consume',
                'params': [True]},
            # Call with positional params
            {'jsonrpc': '2.0', 'method': 'core.tracklist.set_repeat',
                'params': [False], 'id': '2'},
            # Invalid request
            {'foo': 'boo'},
            # Unknown method
            {'jsonrpc': '2.0', 'method': 'foo.get',
                'params': {'name': 'myself'}, 'id': '5'},
            # Call without params
            {'jsonrpc': '2.0', 'method': 'core.tracklist.get_random',
                'id': '9'},
        ]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 5)
        response = dict((row['id'], row) for row in response)
        self.assertEqual(response['1']['result'], False)
        self.assertEqual(response['2']['result'], None)
        self.assertEqual(response[None]['error']['code'], -32600)
        self.assertEqual(response['5']['error']['code'], -32601)
        self.assertEqual(response['9']['result'], False)


class JsonRpcInspectorTest(JsonRpcTestBase):

    def test_empty_object_mounts_is_not_allowed(self):
        with self.assertRaises(AttributeError):
            jsonrpc.JsonRpcInspector(objects={'': Calculator})

    def test_can_describe_method_on_root(self):
        inspector = jsonrpc.JsonRpcInspector({
            'hello': lambda: 'Hello, world!',
        })

        methods = inspector.describe()

        self.assertIn('hello', methods)
        self.assertEqual(len(methods['hello']['params']), 0)

    def test_inspector_can_describe_an_object_with_methods(self):
        inspector = jsonrpc.JsonRpcInspector({
            'calc': Calculator,
        })

        methods = inspector.describe()

        self.assertIn('calc.add', methods)
        self.assertEqual(
            methods['calc.add']['description'],
            'Returns the sum of the given numbers')

        self.assertIn('calc.sub', methods)
        self.assertIn('calc.take_it_all', methods)
        self.assertNotIn('calc._secret', methods)
        self.assertNotIn('calc.__init__', methods)

        method = methods['calc.take_it_all']
        self.assertIn('params', method)

        params = method['params']

        self.assertEqual(params[0]['name'], 'a')
        self.assertNotIn('default', params[0])

        self.assertEqual(params[1]['name'], 'b')
        self.assertNotIn('default', params[1])

        self.assertEqual(params[2]['name'], 'c')
        self.assertEqual(params[2]['default'], True)

        self.assertEqual(params[3]['name'], 'args')
        self.assertNotIn('default', params[3])
        self.assertEqual(params[3]['varargs'], True)

        self.assertEqual(params[4]['name'], 'kwargs')
        self.assertNotIn('default', params[4])
        self.assertEqual(params[4]['kwargs'], True)

    def test_inspector_can_describe_a_bunch_of_large_classes(self):
        inspector = jsonrpc.JsonRpcInspector({
            'core.get_uri_schemes': core.Core.get_uri_schemes,
            'core.library': core.LibraryController,
            'core.playback': core.PlaybackController,
            'core.playlists': core.PlaylistsController,
            'core.tracklist': core.TracklistController,
        })

        methods = inspector.describe()

        self.assertIn('core.get_uri_schemes', methods)
        self.assertEqual(len(methods['core.get_uri_schemes']['params']), 0)

        self.assertIn('core.library.lookup', methods.keys())
        self.assertEqual(
            methods['core.library.lookup']['params'][0]['name'], 'uri')

        self.assertIn('core.playback.next', methods)
        self.assertEqual(len(methods['core.playback.next']['params']), 0)

        self.assertIn('core.playlists.get_playlists', methods)
        self.assertEqual(
            len(methods['core.playlists.get_playlists']['params']), 1)

        self.assertIn('core.tracklist.filter', methods.keys())
        self.assertEqual(
            methods['core.tracklist.filter']['params'][0]['name'], 'criteria')
        self.assertEqual(
            methods['core.tracklist.filter']['params'][1]['name'], 'kwargs')
        self.assertEqual(
            methods['core.tracklist.filter']['params'][1]['kwargs'], True)
