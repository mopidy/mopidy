# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import re
import unittest

from mock import Mock, sentinel

from mopidy import compat
from mopidy.internal import network

from tests import any_unicode


class LineProtocolTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.mock = Mock(spec=network.LineProtocol)

        self.mock.terminator = network.LineProtocol.terminator
        self.mock.encoding = network.LineProtocol.encoding
        self.mock.delimiter = network.LineProtocol.delimiter
        self.mock.prevent_timeout = False

    def test_init_stores_values_in_attributes(self):
        delimiter = re.compile(network.LineProtocol.terminator)
        network.LineProtocol.__init__(self.mock, sentinel.connection)
        self.assertEqual(sentinel.connection, self.mock.connection)
        self.assertEqual('', self.mock.recv_buffer)
        self.assertEqual(delimiter, self.mock.delimiter)
        self.assertFalse(self.mock.prevent_timeout)

    def test_init_compiles_delimiter(self):
        self.mock.delimiter = '\r?\n'
        delimiter = re.compile('\r?\n')

        network.LineProtocol.__init__(self.mock, sentinel.connection)
        self.assertEqual(delimiter, self.mock.delimiter)

    def test_on_receive_close_calls_stop(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []

        network.LineProtocol.on_receive(self.mock, {'close': True})
        self.mock.connection.stop.assert_called_once_with(any_unicode)

    def test_on_receive_no_new_lines_adds_to_recv_buffer(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []

        network.LineProtocol.on_receive(self.mock, {'received': 'data'})
        self.assertEqual('data', self.mock.recv_buffer)
        self.mock.parse_lines.assert_called_once_with()
        self.assertEqual(0, self.mock.on_line_received.call_count)

    def test_on_receive_toggles_timeout(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []

        network.LineProtocol.on_receive(self.mock, {'received': 'data'})
        self.mock.connection.disable_timeout.assert_called_once_with()
        self.mock.connection.enable_timeout.assert_called_once_with()

    def test_on_receive_toggles_unless_prevent_timeout_is_set(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []
        self.mock.prevent_timeout = True

        network.LineProtocol.on_receive(self.mock, {'received': 'data'})
        self.mock.connection.disable_timeout.assert_called_once_with()
        self.assertEqual(0, self.mock.connection.enable_timeout.call_count)

    def test_on_receive_no_new_lines_calls_parse_lines(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []

        network.LineProtocol.on_receive(self.mock, {'received': 'data'})
        self.mock.parse_lines.assert_called_once_with()
        self.assertEqual(0, self.mock.on_line_received.call_count)

    def test_on_receive_with_new_line_calls_decode(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = [sentinel.line]

        network.LineProtocol.on_receive(self.mock, {'received': 'data\n'})
        self.mock.parse_lines.assert_called_once_with()
        self.mock.decode.assert_called_once_with(sentinel.line)

    def test_on_receive_with_new_line_calls_on_recieve(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = [sentinel.line]
        self.mock.decode.return_value = sentinel.decoded

        network.LineProtocol.on_receive(self.mock, {'received': 'data\n'})
        self.mock.on_line_received.assert_called_once_with(sentinel.decoded)

    def test_on_receive_with_new_line_with_failed_decode(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = [sentinel.line]
        self.mock.decode.return_value = None

        network.LineProtocol.on_receive(self.mock, {'received': 'data\n'})
        self.assertEqual(0, self.mock.on_line_received.call_count)

    def test_on_receive_with_new_lines_calls_on_recieve(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = ['line1', 'line2']
        self.mock.decode.return_value = sentinel.decoded

        network.LineProtocol.on_receive(
            self.mock, {'received': 'line1\nline2\n'})
        self.assertEqual(2, self.mock.on_line_received.call_count)

    def test_parse_lines_emtpy_buffer(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = ''

        lines = network.LineProtocol.parse_lines(self.mock)
        with self.assertRaises(StopIteration):
            lines.next()

    def test_parse_lines_no_terminator(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = 'data'

        lines = network.LineProtocol.parse_lines(self.mock)
        with self.assertRaises(StopIteration):
            lines.next()

    def test_parse_lines_termintor(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = 'data\n'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data', lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_termintor_with_carriage_return(self):
        self.mock.delimiter = re.compile(r'\r?\n')
        self.mock.recv_buffer = 'data\r\n'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data', lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_no_data_before_terminator(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = '\n'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('', lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_extra_data_after_terminator(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = 'data1\ndata2'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data1', lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('data2', self.mock.recv_buffer)

    def test_parse_lines_unicode(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = 'æøå\n'.encode('utf-8')

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('æøå'.encode('utf-8'), lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_multiple_lines(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = 'abc\ndef\nghi\njkl'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('abc', lines.next())
        self.assertEqual('def', lines.next())
        self.assertEqual('ghi', lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('jkl', self.mock.recv_buffer)

    def test_parse_lines_multiple_calls(self):
        self.mock.delimiter = re.compile(r'\n')
        self.mock.recv_buffer = 'data1'

        lines = network.LineProtocol.parse_lines(self.mock)
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('data1', self.mock.recv_buffer)

        self.mock.recv_buffer += '\ndata2'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data1', lines.next())
        with self.assertRaises(StopIteration):
            lines.next()
        self.assertEqual('data2', self.mock.recv_buffer)

    def test_send_lines_called_with_no_lines(self):
        self.mock.connection = Mock(spec=network.Connection)

        network.LineProtocol.send_lines(self.mock, [])
        self.assertEqual(0, self.mock.encode.call_count)
        self.assertEqual(0, self.mock.connection.queue_send.call_count)

    def test_send_lines_calls_join_lines(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = 'lines'

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.join_lines.assert_called_once_with(sentinel.lines)

    def test_send_line_encodes_joined_lines_with_final_terminator(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = 'lines\n'

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.encode.assert_called_once_with('lines\n')

    def test_send_lines_sends_encoded_string(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = 'lines'
        self.mock.encode.return_value = sentinel.data

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.connection.queue_send.assert_called_once_with(sentinel.data)

    def test_join_lines_returns_empty_string_for_no_lines(self):
        self.assertEqual('', network.LineProtocol.join_lines(self.mock, []))

    def test_join_lines_returns_joined_lines(self):
        self.assertEqual('1\n2\n', network.LineProtocol.join_lines(
            self.mock, ['1', '2']))

    def test_decode_calls_decode_on_string(self):
        string = Mock()

        network.LineProtocol.decode(self.mock, string)
        string.decode.assert_called_once_with(self.mock.encoding)

    def test_decode_plain_ascii(self):
        result = network.LineProtocol.decode(self.mock, 'abc')
        self.assertEqual('abc', result)
        self.assertEqual(compat.text_type, type(result))

    def test_decode_utf8(self):
        result = network.LineProtocol.decode(
            self.mock, 'æøå'.encode('utf-8'))
        self.assertEqual('æøå', result)
        self.assertEqual(compat.text_type, type(result))

    def test_decode_invalid_data(self):
        string = Mock()
        string.decode.side_effect = UnicodeError

        network.LineProtocol.decode(self.mock, string)
        self.mock.stop.assert_called_once_with()

    def test_encode_calls_encode_on_string(self):
        string = Mock()

        network.LineProtocol.encode(self.mock, string)
        string.encode.assert_called_once_with(self.mock.encoding)

    def test_encode_plain_ascii(self):
        result = network.LineProtocol.encode(self.mock, 'abc')
        self.assertEqual('abc', result)
        self.assertEqual(str, type(result))

    def test_encode_utf8(self):
        result = network.LineProtocol.encode(self.mock, 'æøå')
        self.assertEqual('æøå'.encode('utf-8'), result)
        self.assertEqual(str, type(result))

    def test_encode_invalid_data(self):
        string = Mock()
        string.encode.side_effect = UnicodeError

        network.LineProtocol.encode(self.mock, string)
        self.mock.stop.assert_called_once_with()

    def test_host_property(self):
        mock = Mock(spec=network.Connection)
        mock.host = sentinel.host

        lineprotocol = network.LineProtocol(mock)
        self.assertEqual(sentinel.host, lineprotocol.host)

    def test_port_property(self):
        mock = Mock(spec=network.Connection)
        mock.port = sentinel.port

        lineprotocol = network.LineProtocol(mock)
        self.assertEqual(sentinel.port, lineprotocol.port)
