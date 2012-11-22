from __future__ import unicode_literals

import json

import pykka
import mock

from mopidy import core, models
from mopidy.backends import dummy
from mopidy.utils import jsonrpc

from tests import unittest


class Calculator(object):
    def model(self):
        return 'TI83'

    def add(self, a, b):
        return a + b

    def sub(self, a, b):
        return a - b

    def describe(self):
        return {
            'add': 'Returns the sum of the terms',
            'sub': 'Returns the diff of the terms',
        }

    def _secret(self):
        return 'Grand Unified Theory'


class JsonRpcTestBase(unittest.TestCase):
    def setUp(self):
        self.backend = dummy.DummyBackend.start(audio=None).proxy()
        self.core = core.Core.start(backends=[self.backend]).proxy()
        self.jrw = jsonrpc.JsonRpcWrapper(
            objects={
                'core': self.core,
                'calculator': Calculator(),
            },
            encoders=[models.ModelJSONEncoder],
            decoders=[models.model_json_decoder])

    def tearDown(self):
        pykka.ActorRegistry.stop_all()


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
        response = self.jrw.handle_json(request)

        self.assertEqual(
            response, '{"foo": {"__model__": "Artist", "name": "bar"}}')

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
    def test_call_method_on_plain_object(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calculator.model',
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
            'method': 'calculator.describe',
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
            'method': 'core.playback.get_volume',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['result'], None)

    def test_call_method_with_positional_params(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.playback.set_volume',
            'params': [37],
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['result'], None)
        self.assertEqual(self.core.playback.get_volume().get(), 37)

    def test_call_methods_with_named_params(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.playback.set_volume',
            'params': {'volume': 37},
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertEqual(response['result'], None)
        self.assertEqual(self.core.playback.get_volume().get(), 37)


class JsonRpcSingleNotificationTest(JsonRpcTestBase):
    def test_notification_does_not_return_a_result(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.get_uri_schemes',
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)

    def test_notification_makes_an_observable_change(self):
        self.assertEqual(self.core.playback.get_volume().get(), None)

        request = {
            'jsonrpc': '2.0',
            'method': 'core.playback.set_volume',
            'params': [37],
        }
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)
        self.assertEqual(self.core.playback.get_volume().get(), 37)

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
        self.core.playback.set_random(True).get()

        request = [
            {'jsonrpc': '2.0', 'method': 'core.playback.get_repeat', 'id': 1},
            {'jsonrpc': '2.0', 'method': 'core.playback.get_random', 'id': 2},
            {'jsonrpc': '2.0', 'method': 'core.playback.get_single', 'id': 3},
        ]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 3)

        response = {row['id']: row for row in response}
        self.assertEqual(response[1]['result'], False)
        self.assertEqual(response[2]['result'], True)
        self.assertEqual(response[3]['result'], False)

    def test_batch_of_commands_and_notifications_returns_some(self):
        self.core.playback.set_random(True).get()

        request = [
            {'jsonrpc': '2.0', 'method': 'core.playback.get_repeat'},
            {'jsonrpc': '2.0', 'method': 'core.playback.get_random', 'id': 2},
            {'jsonrpc': '2.0', 'method': 'core.playback.get_single', 'id': 3},
        ]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 2)

        response = {row['id']: row for row in response}
        self.assertNotIn(1, response)
        self.assertEqual(response[2]['result'], True)
        self.assertEqual(response[3]['result'], False)

    def test_batch_of_only_notifications_returns_nothing(self):
        self.core.playback.set_random(True).get()

        request = [
            {'jsonrpc': '2.0', 'method': 'core.playback.get_repeat'},
            {'jsonrpc': '2.0', 'method': 'core.playback.get_random'},
            {'jsonrpc': '2.0', 'method': 'core.playback.get_single'},
        ]
        response = self.jrw.handle_data(request)

        self.assertIsNone(response)


class JsonRpcSingleCommandErrorTest(JsonRpcTestBase):
    def test_application_error_response(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'core.tracklist.index',
            'params': ['bogus'],
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        self.assertNotIn('result', response)

        error = response['error']
        self.assertEqual(error['code'], 0)
        self.assertEqual(error['message'], 'Application error')

        data = error['data']
        self.assertEqual(data['type'], 'ValueError')
        self.assertEqual(data['message'], "u'bogus' is not in list")
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

    def test_unknown_method_causes_unknown_method_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'bogus',
            'params': ['bogus'],
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32601)
        self.assertEqual(error['message'], 'Method not found')

    def test_private_method_causes_unknown_method_error(self):
        request = {
            'jsonrpc': '2.0',
            'method': 'calculator._secret',
            'id': 1,
        }
        response = self.jrw.handle_data(request)

        error = response['error']
        self.assertEqual(error['code'], -32601)
        self.assertEqual(error['message'], 'Method not found')

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
            {'jsonrpc': '2.0', 'method': 'core.playback.set_volume',
                'params': [47], 'id': '1'},
            # Notification
            {'jsonrpc': '2.0', 'method': 'core.playback.set_consume',
                'params': [True]},
            # Call with positional params
            {'jsonrpc': '2.0', 'method': 'core.playback.set_repeat',
                'params': [False], 'id': '2'},
            # Invalid request
            {'foo': 'boo'},
            # Unknown method
            {'jsonrpc': '2.0', 'method': 'foo.get',
                'params': {'name': 'myself'}, 'id': '5'},
            # Call without params
            {'jsonrpc': '2.0', 'method': 'core.playback.get_random',
                'id': '9'},
        ]
        response = self.jrw.handle_data(request)

        self.assertEqual(len(response), 5)
        response = {row['id']: row for row in response}
        self.assertEqual(response['1']['result'], None)
        self.assertEqual(response['2']['result'], None)
        self.assertEqual(response[None]['error']['code'], -32600)
        self.assertEqual(response['5']['error']['code'], -32601)
        self.assertEqual(response['9']['result'], False)
