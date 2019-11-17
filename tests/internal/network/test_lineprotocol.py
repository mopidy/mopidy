import re
import unittest
from unittest.mock import Mock, sentinel

from mopidy.internal import network

from tests import any_unicode


class LineProtocolTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.mock = Mock(spec=network.LineProtocol)

        self.mock.terminator = network.LineProtocol.terminator
        self.mock.encoding = network.LineProtocol.encoding
        self.mock.delimiter = network.LineProtocol.delimiter
        self.mock.prevent_timeout = False

    def prepare_on_receive_test(self, return_value=None):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = b""
        self.mock.parse_lines.return_value = return_value or []

    def test_init_stores_values_in_attributes(self):
        delimiter = re.compile(network.LineProtocol.terminator)
        network.LineProtocol.__init__(self.mock, sentinel.connection)
        assert sentinel.connection == self.mock.connection
        assert b"" == self.mock.recv_buffer
        assert delimiter == self.mock.delimiter
        assert not self.mock.prevent_timeout

    def test_init_compiles_delimiter(self):
        self.mock.delimiter = "\r?\n"
        delimiter = re.compile("\r?\n")

        network.LineProtocol.__init__(self.mock, sentinel.connection)
        assert delimiter == self.mock.delimiter

    def test_on_receive_close_calls_stop(self):
        self.prepare_on_receive_test()

        network.LineProtocol.on_receive(self.mock, {"close": True})
        self.mock.connection.stop.assert_called_once_with(any_unicode)

    def test_on_receive_no_new_lines_adds_to_recv_buffer(self):
        self.prepare_on_receive_test()

        network.LineProtocol.on_receive(self.mock, {"received": b"data"})
        assert b"data" == self.mock.recv_buffer
        self.mock.parse_lines.assert_called_once_with()
        assert 0 == self.mock.on_line_received.call_count

    def test_on_receive_toggles_timeout(self):
        self.prepare_on_receive_test()

        network.LineProtocol.on_receive(self.mock, {"received": b"data"})
        self.mock.connection.disable_timeout.assert_called_once_with()
        self.mock.connection.enable_timeout.assert_called_once_with()

    def test_on_receive_toggles_unless_prevent_timeout_is_set(self):
        self.prepare_on_receive_test()
        self.mock.prevent_timeout = True

        network.LineProtocol.on_receive(self.mock, {"received": b"data"})
        self.mock.connection.disable_timeout.assert_called_once_with()
        assert 0 == self.mock.connection.enable_timeout.call_count

    def test_on_receive_no_new_lines_calls_parse_lines(self):
        self.prepare_on_receive_test()

        network.LineProtocol.on_receive(self.mock, {"received": b"data"})
        self.mock.parse_lines.assert_called_once_with()
        assert 0 == self.mock.on_line_received.call_count

    def test_on_receive_with_new_line_calls_decode(self):
        self.prepare_on_receive_test([sentinel.line])

        network.LineProtocol.on_receive(self.mock, {"received": b"data\n"})
        self.mock.parse_lines.assert_called_once_with()
        self.mock.decode.assert_called_once_with(sentinel.line)

    def test_on_receive_with_new_line_calls_on_recieve(self):
        self.prepare_on_receive_test([sentinel.line])
        self.mock.decode.return_value = sentinel.decoded

        network.LineProtocol.on_receive(self.mock, {"received": b"data\n"})
        self.mock.on_line_received.assert_called_once_with(sentinel.decoded)

    def test_on_receive_with_new_line_with_failed_decode(self):
        self.prepare_on_receive_test([sentinel.line])
        self.mock.decode.return_value = None

        network.LineProtocol.on_receive(self.mock, {"received": b"data\n"})
        assert 0 == self.mock.on_line_received.call_count

    def test_on_receive_with_new_lines_calls_on_recieve(self):
        self.prepare_on_receive_test(["line1", "line2"])
        self.mock.decode.return_value = sentinel.decoded

        network.LineProtocol.on_receive(
            self.mock, {"received": b"line1\nline2\n"}
        )
        assert 2 == self.mock.on_line_received.call_count

    def test_on_failure_calls_stop(self):
        self.mock.connection = Mock(spec=network.Connection)

        network.LineProtocol.on_failure(self.mock, None, None, None)
        self.mock.connection.stop.assert_called_once_with("Actor failed.")

    def prepare_parse_lines_test(self, recv_data=""):
        self.mock.terminator = b"\n"
        self.mock.delimiter = re.compile(br"\n")
        self.mock.recv_buffer = recv_data.encode()

    def test_parse_lines_emtpy_buffer(self):
        self.prepare_parse_lines_test()

        lines = network.LineProtocol.parse_lines(self.mock)
        with self.assertRaises(StopIteration):
            next(lines)

    def test_parse_lines_no_terminator(self):
        self.prepare_parse_lines_test("data")

        lines = network.LineProtocol.parse_lines(self.mock)
        with self.assertRaises(StopIteration):
            next(lines)

    def test_parse_lines_terminator(self):
        self.prepare_parse_lines_test("data\n")

        lines = network.LineProtocol.parse_lines(self.mock)
        assert b"data" == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"" == self.mock.recv_buffer

    def test_parse_lines_terminator_with_carriage_return(self):
        self.prepare_parse_lines_test("data\r\n")
        self.mock.delimiter = re.compile(br"\r?\n")

        lines = network.LineProtocol.parse_lines(self.mock)
        assert b"data" == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"" == self.mock.recv_buffer

    def test_parse_lines_no_data_before_terminator(self):
        self.prepare_parse_lines_test("\n")

        lines = network.LineProtocol.parse_lines(self.mock)
        assert b"" == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"" == self.mock.recv_buffer

    def test_parse_lines_extra_data_after_terminator(self):
        self.prepare_parse_lines_test("data1\ndata2")

        lines = network.LineProtocol.parse_lines(self.mock)
        assert b"data1" == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"data2" == self.mock.recv_buffer

    def test_parse_lines_non_ascii(self):
        self.prepare_parse_lines_test("æøå\n")

        lines = network.LineProtocol.parse_lines(self.mock)
        assert "æøå".encode() == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"" == self.mock.recv_buffer

    def test_parse_lines_multiple_lines(self):
        self.prepare_parse_lines_test("abc\ndef\nghi\njkl")

        lines = network.LineProtocol.parse_lines(self.mock)
        assert b"abc" == next(lines)
        assert b"def" == next(lines)
        assert b"ghi" == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"jkl" == self.mock.recv_buffer

    def test_parse_lines_multiple_calls(self):
        self.prepare_parse_lines_test("data1")

        lines = network.LineProtocol.parse_lines(self.mock)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"data1" == self.mock.recv_buffer

        self.mock.recv_buffer += b"\ndata2"

        lines = network.LineProtocol.parse_lines(self.mock)
        assert b"data1" == next(lines)
        with self.assertRaises(StopIteration):
            next(lines)
        assert b"data2" == self.mock.recv_buffer

    def test_send_lines_called_with_no_lines(self):
        self.mock.connection = Mock(spec=network.Connection)

        network.LineProtocol.send_lines(self.mock, [])
        assert 0 == self.mock.encode.call_count
        assert 0 == self.mock.connection.queue_send.call_count

    def test_send_lines_calls_join_lines(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = "lines"

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.join_lines.assert_called_once_with(sentinel.lines)

    def test_send_line_encodes_joined_lines_with_final_terminator(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = "lines\n"

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.encode.assert_called_once_with("lines\n")

    def test_send_lines_sends_encoded_string(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = "lines"
        self.mock.encode.return_value = sentinel.data

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.connection.queue_send.assert_called_once_with(sentinel.data)

    def test_join_lines_returns_empty_string_for_no_lines(self):
        assert "" == network.LineProtocol.join_lines(self.mock, [])

    def test_join_lines_returns_joined_lines(self):
        self.mock.decode.return_value = "\n"
        assert "1\n2\n" == network.LineProtocol.join_lines(
            self.mock, ["1", "2"]
        )

    def test_decode_calls_decode_on_string(self):
        string = Mock()

        network.LineProtocol.decode(self.mock, string)
        string.decode.assert_called_once_with(self.mock.encoding)

    def test_decode_plain_ascii(self):
        result = network.LineProtocol.decode(self.mock, b"abc")
        assert "abc" == result
        assert str == type(result)

    def test_decode_utf8(self):
        result = network.LineProtocol.decode(self.mock, "æøå".encode())
        assert "æøå" == result
        assert str == type(result)

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
        result = network.LineProtocol.encode(self.mock, "abc")
        assert b"abc" == result
        assert bytes == type(result)

    def test_encode_utf8(self):
        result = network.LineProtocol.encode(self.mock, "æøå")
        assert "æøå".encode() == result
        assert bytes == type(result)

    def test_encode_invalid_data(self):
        string = Mock()
        string.encode.side_effect = UnicodeError

        network.LineProtocol.encode(self.mock, string)
        self.mock.stop.assert_called_once_with()

    def test_host_property(self):
        mock = Mock(spec=network.Connection)
        mock.host = sentinel.host

        lineprotocol = network.LineProtocol(mock)
        assert sentinel.host == lineprotocol.host

    def test_port_property(self):
        mock = Mock(spec=network.Connection)
        mock.port = sentinel.port

        lineprotocol = network.LineProtocol(mock)
        assert sentinel.port == lineprotocol.port
