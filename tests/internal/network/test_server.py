from __future__ import absolute_import, unicode_literals

import errno
import os
import socket
import unittest

from mock import Mock, patch, sentinel

from mopidy import exceptions
from mopidy.internal import network
from mopidy.internal.gi import GLib

from tests import any_int


class ServerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.mock = Mock(spec=network.Server)

    def test_init_calls_create_server_socket(self):
        network.Server.__init__(
            self.mock, sentinel.host, sentinel.port, sentinel.protocol)
        self.mock.create_server_socket.assert_called_once_with(
            sentinel.host, sentinel.port)
        self.mock.stop()

    def test_init_calls_register_server(self):
        sock = Mock(spec=socket.SocketType)
        sock.fileno.return_value = sentinel.fileno
        self.mock.create_server_socket.return_value = sock

        network.Server.__init__(
            self.mock, sentinel.host, sentinel.port, sentinel.protocol)
        self.mock.register_server_socket.assert_called_once_with(
            sentinel.fileno)

    def test_init_fails_on_fileno_call(self):
        sock = Mock(spec=socket.SocketType)
        sock.fileno.side_effect = socket.error
        self.mock.create_server_socket.return_value = sock

        with self.assertRaises(socket.error):
            network.Server.__init__(
                self.mock, sentinel.host, sentinel.port, sentinel.protocol)

    def test_init_stores_values_in_attributes(self):
        # This need to be a mock and no a sentinel as fileno() is called on it
        sock = Mock(spec=socket.SocketType)
        self.mock.create_server_socket.return_value = sock

        network.Server.__init__(
            self.mock, sentinel.host, sentinel.port, sentinel.protocol,
            max_connections=sentinel.max_connections, timeout=sentinel.timeout)
        self.assertEqual(sentinel.protocol, self.mock.protocol)
        self.assertEqual(sentinel.max_connections, self.mock.max_connections)
        self.assertEqual(sentinel.timeout, self.mock.timeout)
        self.assertEqual(sock, self.mock.server_socket)

    def test_create_server_socket_no_port(self):
        with self.assertRaises(exceptions.ValidationError):
            network.Server.create_server_socket(
                self.mock, str(sentinel.host), None)

    def test_create_server_socket_invalid_port(self):
        with self.assertRaises(exceptions.ValidationError):
            network.Server.create_server_socket(
                self.mock, str(sentinel.host), str(sentinel.port))

    @patch.object(network, 'create_tcp_socket', spec=socket.SocketType)
    def test_create_server_socket_sets_up_listener(self, create_tcp_socket):
        sock = create_tcp_socket.return_value

        network.Server.create_server_socket(
            self.mock, str(sentinel.host), 1234)
        sock.setblocking.assert_called_once_with(False)
        sock.bind.assert_called_once_with((str(sentinel.host), 1234))
        sock.listen.assert_called_once_with(any_int)
        create_tcp_socket.assert_called_once()

    @patch.object(network, 'create_unix_socket', spec=socket.SocketType)
    def test_create_server_socket_sets_up_listener_unix(
            self,
            create_unix_socket):
        sock = create_unix_socket.return_value

        network.Server.create_server_socket(
            self.mock, 'unix:' + str(sentinel.host), sentinel.port)
        sock.setblocking.assert_called_once_with(False)
        sock.bind.assert_called_once_with(str(sentinel.host))
        sock.listen.assert_called_once_with(any_int)
        create_unix_socket.assert_called_once()

    @patch.object(network, 'create_tcp_socket', new=Mock())
    def test_create_server_socket_fails(self):
        network.create_tcp_socket.side_effect = socket.error
        with self.assertRaises(socket.error):
            network.Server.create_server_socket(
                self.mock, str(sentinel.host), 1234)

    @patch.object(network, 'create_unix_socket', new=Mock())
    def test_create_server_socket_fails_unix(self):
        network.create_unix_socket.side_effect = socket.error
        with self.assertRaises(socket.error):
            network.Server.create_server_socket(
                self.mock, 'unix:' + str(sentinel.host), sentinel.port)

    @patch.object(network, 'create_tcp_socket', new=Mock())
    def test_create_server_bind_fails(self):
        sock = network.create_tcp_socket.return_value
        sock.bind.side_effect = socket.error

        with self.assertRaises(socket.error):
            network.Server.create_server_socket(
                self.mock, str(sentinel.host), 1234)

    @patch.object(network, 'create_unix_socket', new=Mock())
    def test_create_server_bind_fails_unix(self):
        sock = network.create_unix_socket.return_value
        sock.bind.side_effect = socket.error

        with self.assertRaises(socket.error):
            network.Server.create_server_socket(
                self.mock, 'unix:' + str(sentinel.host), sentinel.port)

    @patch.object(network, 'create_tcp_socket', new=Mock())
    def test_create_server_listen_fails(self):
        sock = network.create_tcp_socket.return_value
        sock.listen.side_effect = socket.error

        with self.assertRaises(socket.error):
            network.Server.create_server_socket(
                self.mock, str(sentinel.host), 1234)

    @patch.object(network, 'create_unix_socket', new=Mock())
    def test_create_server_listen_fails_unix(self):
        sock = network.create_unix_socket.return_value
        sock.listen.side_effect = socket.error

        with self.assertRaises(socket.error):
            network.Server.create_server_socket(
                self.mock, 'unix:' + str(sentinel.host), sentinel.port)

    @patch.object(os, 'unlink', new=Mock())
    @patch.object(GLib, 'source_remove', new=Mock())
    def test_stop_server_cleans_unix_socket(self):
        self.mock.watcher = Mock()
        sock = Mock()
        sock.family = socket.AF_UNIX
        self.mock.server_socket = sock
        network.Server.stop(self.mock)
        os.unlink.assert_called_once_with(sock.getsockname())

    @patch.object(GLib, 'io_add_watch', new=Mock())
    def test_register_server_socket_sets_up_io_watch(self):
        network.Server.register_server_socket(self.mock, sentinel.fileno)
        GLib.io_add_watch.assert_called_once_with(
            sentinel.fileno, GLib.IO_IN, self.mock.handle_connection)

    def test_handle_connection(self):
        self.mock.accept_connection.return_value = (
            sentinel.sock, sentinel.addr)
        self.mock.maximum_connections_exceeded.return_value = False

        self.assertTrue(network.Server.handle_connection(
            self.mock, sentinel.fileno, GLib.IO_IN))
        self.mock.accept_connection.assert_called_once_with()
        self.mock.maximum_connections_exceeded.assert_called_once_with()
        self.mock.init_connection.assert_called_once_with(
            sentinel.sock, sentinel.addr)
        self.assertEqual(0, self.mock.reject_connection.call_count)

    def test_handle_connection_exceeded_connections(self):
        self.mock.accept_connection.return_value = (
            sentinel.sock, sentinel.addr)
        self.mock.maximum_connections_exceeded.return_value = True

        self.assertTrue(network.Server.handle_connection(
            self.mock, sentinel.fileno, GLib.IO_IN))
        self.mock.accept_connection.assert_called_once_with()
        self.mock.maximum_connections_exceeded.assert_called_once_with()
        self.mock.reject_connection.assert_called_once_with(
            sentinel.sock, sentinel.addr)
        self.assertEqual(0, self.mock.init_connection.call_count)

    def test_accept_connection(self):
        sock = Mock(spec=socket.SocketType)
        connected_sock = Mock(spec=socket.SocketType)
        sock.accept.return_value = (connected_sock, sentinel.addr)
        self.mock.server_socket = sock

        sock, addr = network.Server.accept_connection(self.mock)
        self.assertEqual(connected_sock, sock)
        self.assertEqual(sentinel.addr, addr)

    def test_accept_connection_unix(self):
        sock = Mock(spec=socket.SocketType)
        connected_sock = Mock(spec=socket.SocketType)
        connected_sock.family = socket.AF_UNIX
        connected_sock.getsockname.return_value = sentinel.sockname
        sock.accept.return_value = (connected_sock, sentinel.addr)
        self.mock.server_socket = sock

        sock, addr = network.Server.accept_connection(self.mock)
        self.assertEqual(connected_sock, sock)
        self.assertEqual((sentinel.sockname, None), addr)

    def test_accept_connection_recoverable_error(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.server_socket = sock

        for error in (errno.EAGAIN, errno.EINTR):
            sock.accept.side_effect = socket.error(error, '')
            with self.assertRaises(network.ShouldRetrySocketCall):
                network.Server.accept_connection(self.mock)

    # FIXME decide if this should be allowed to propegate
    def test_accept_connection_unrecoverable_error(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.server_socket = sock
        sock.accept.side_effect = socket.error
        with self.assertRaises(socket.error):
            network.Server.accept_connection(self.mock)

    def test_maximum_connections_exceeded(self):
        self.mock.max_connections = 10

        self.mock.number_of_connections.return_value = 11
        self.assertTrue(network.Server.maximum_connections_exceeded(self.mock))

        self.mock.number_of_connections.return_value = 10
        self.assertTrue(network.Server.maximum_connections_exceeded(self.mock))

        self.mock.number_of_connections.return_value = 9
        self.assertFalse(
            network.Server.maximum_connections_exceeded(self.mock))

    @patch('pykka.ActorRegistry.get_by_class')
    def test_number_of_connections(self, get_by_class):
        self.mock.protocol = sentinel.protocol

        get_by_class.return_value = [1, 2, 3]
        self.assertEqual(3, network.Server.number_of_connections(self.mock))

        get_by_class.return_value = []
        self.assertEqual(0, network.Server.number_of_connections(self.mock))

    @patch.object(network, 'Connection', new=Mock())
    def test_init_connection(self):
        self.mock.protocol = sentinel.protocol
        self.mock.protocol_kwargs = {}
        self.mock.timeout = sentinel.timeout

        network.Server.init_connection(self.mock, sentinel.sock, sentinel.addr)
        network.Connection.assert_called_once_with(
            sentinel.protocol, {}, sentinel.sock, sentinel.addr,
            sentinel.timeout)

    @patch.object(network, 'format_socket_name', new=Mock())
    def test_reject_connection(self):
        sock = Mock(spec=socket.SocketType)

        network.Server.reject_connection(
            self.mock, sock, (sentinel.host, sentinel.port))
        sock.close.assert_called_once_with()

    @patch.object(network, 'format_socket_name', new=Mock())
    def test_reject_connection_error(self):
        sock = Mock(spec=socket.SocketType)
        sock.close.side_effect = socket.error

        network.Server.reject_connection(
            self.mock, sock, (sentinel.host, sentinel.port))
        sock.close.assert_called_once_with()
