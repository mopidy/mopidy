import errno
import gobject
import socket
from mock import patch, sentinel, Mock

from mopidy.utils import network

from tests import unittest, any_int


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.mock = Mock(spec=network.Server)

    def test_init_calls_create_server_socket(self):
        network.Server.__init__(self.mock, sentinel.host,
            sentinel.port, sentinel.protocol)
        self.mock.create_server_socket.assert_called_once_with(
            sentinel.host, sentinel.port)

    def test_init_calls_register_server(self):
        sock = Mock(spec=socket.SocketType)
        sock.fileno.return_value = sentinel.fileno
        self.mock.create_server_socket.return_value = sock

        network.Server.__init__(self.mock, sentinel.host,
            sentinel.port, sentinel.protocol)
        self.mock.register_server_socket.assert_called_once_with(
            sentinel.fileno)

    def test_init_fails_on_fileno_call(self):
        sock = Mock(spec=socket.SocketType)
        sock.fileno.side_effect = socket.error
        self.mock.create_server_socket.return_value = sock

        self.assertRaises(socket.error, network.Server.__init__,
            self.mock, sentinel.host, sentinel.port, sentinel.protocol)

    def test_init_stores_values_in_attributes(self):
        # This need to be a mock and no a sentinel as fileno() is called on it
        sock = Mock(spec=socket.SocketType)
        self.mock.create_server_socket.return_value = sock

        network.Server.__init__(self.mock, sentinel.host, sentinel.port,
            sentinel.protocol, max_connections=sentinel.max_connections,
            timeout=sentinel.timeout)
        self.assertEqual(sentinel.protocol, self.mock.protocol)
        self.assertEqual(sentinel.max_connections, self.mock.max_connections)
        self.assertEqual(sentinel.timeout, self.mock.timeout)
        self.assertEqual(sock, self.mock.server_socket)

    @patch.object(network, 'create_socket', spec=socket.SocketType)
    def test_create_server_socket_sets_up_listener(self, create_socket):
        sock = create_socket.return_value

        network.Server.create_server_socket(self.mock,
            sentinel.host, sentinel.port)
        sock.setblocking.assert_called_once_with(False)
        sock.bind.assert_called_once_with((sentinel.host, sentinel.port))
        sock.listen.assert_called_once_with(any_int)

    @patch.object(network, 'create_socket', new=Mock())
    def test_create_server_socket_fails(self):
        network.create_socket.side_effect = socket.error
        self.assertRaises(socket.error, network.Server.create_server_socket,
            self.mock, sentinel.host, sentinel.port)

    @patch.object(network, 'create_socket', new=Mock())
    def test_create_server_bind_fails(self):
        sock = network.create_socket.return_value
        sock.bind.side_effect = socket.error

        self.assertRaises(socket.error, network.Server.create_server_socket,
            self.mock, sentinel.host, sentinel.port)

    @patch.object(network, 'create_socket', new=Mock())
    def test_create_server_listen_fails(self):
        sock = network.create_socket.return_value
        sock.listen.side_effect = socket.error

        self.assertRaises(socket.error, network.Server.create_server_socket,
            self.mock, sentinel.host, sentinel.port)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_register_server_socket_sets_up_io_watch(self):
        network.Server.register_server_socket(self.mock, sentinel.fileno)
        gobject.io_add_watch.assert_called_once_with(sentinel.fileno,
            gobject.IO_IN, self.mock.handle_connection)

    def test_handle_connection(self):
        self.mock.accept_connection.return_value = (
            sentinel.sock, sentinel.addr)
        self.mock.maximum_connections_exceeded.return_value = False

        self.assertTrue(network.Server.handle_connection(
            self.mock, sentinel.fileno, gobject.IO_IN))
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
            self.mock, sentinel.fileno, gobject.IO_IN))
        self.mock.accept_connection.assert_called_once_with()
        self.mock.maximum_connections_exceeded.assert_called_once_with()
        self.mock.reject_connection.assert_called_once_with(
            sentinel.sock, sentinel.addr)
        self.assertEqual(0, self.mock.init_connection.call_count)

    def test_accept_connection(self):
        sock = Mock(spec=socket.SocketType)
        sock.accept.return_value = (sentinel.sock, sentinel.addr)
        self.mock.server_socket = sock

        sock, addr = network.Server.accept_connection(self.mock)
        self.assertEqual(sentinel.sock, sock)
        self.assertEqual(sentinel.addr, addr)

    def test_accept_connection_recoverable_error(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.server_socket = sock

        for error in (errno.EAGAIN, errno.EINTR):
            sock.accept.side_effect = socket.error(error, '')
            self.assertRaises(network.ShouldRetrySocketCall,
                network.Server.accept_connection, self.mock)

    # FIXME decide if this should be allowed to propegate
    def test_accept_connection_unrecoverable_error(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.server_socket = sock
        sock.accept.side_effect = socket.error
        self.assertRaises(socket.error,
            network.Server.accept_connection, self.mock)

    def test_maximum_connections_exceeded(self):
        self.mock.max_connections = 10

        self.mock.number_of_connections.return_value = 11
        self.assertTrue(network.Server.maximum_connections_exceeded(self.mock))

        self.mock.number_of_connections.return_value = 10
        self.assertTrue(network.Server.maximum_connections_exceeded(self.mock))

        self.mock.number_of_connections.return_value = 9
        self.assertFalse(network.Server.maximum_connections_exceeded(self.mock))

    @patch('pykka.registry.ActorRegistry.get_by_class')
    def test_number_of_connections(self, get_by_class):
        self.mock.protocol = sentinel.protocol

        get_by_class.return_value = [1, 2, 3]
        self.assertEqual(3, network.Server.number_of_connections(self.mock))

        get_by_class.return_value = []
        self.assertEqual(0, network.Server.number_of_connections(self.mock))

    @patch.object(network, 'Connection', new=Mock())
    def test_init_connection(self):
        self.mock.protocol = sentinel.protocol
        self.mock.timeout = sentinel.timeout

        network.Server.init_connection(self.mock, sentinel.sock, sentinel.addr)
        network.Connection.assert_called_once_with(sentinel.protocol,
            sentinel.sock, sentinel.addr, sentinel.timeout)

    def test_reject_connection(self):
        sock = Mock(spec=socket.SocketType)

        network.Server.reject_connection(self.mock, sock,
            (sentinel.host, sentinel.port))
        sock.close.assert_called_once_with()

    def test_reject_connection_error(self):
        sock = Mock(spec=socket.SocketType)
        sock.close.side_effect = socket.error

        network.Server.reject_connection(self.mock, sock,
            (sentinel.host, sentinel.port))
        sock.close.assert_called_once_with()
