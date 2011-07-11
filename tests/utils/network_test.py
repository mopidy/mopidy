import errno
import gobject
import socket
import unittest
from mock import patch, sentinel, Mock

from mopidy.utils import network

from tests import SkipTest

class FormatHostnameTest(unittest.TestCase):
    @patch('mopidy.utils.network.has_ipv6', True)
    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        network.has_ipv6 = True
        self.assertEqual(network.format_hostname('0.0.0.0'), '::ffff:0.0.0.0')
        self.assertEqual(network.format_hostname('1.0.0.1'), '::ffff:1.0.0.1')

    @patch('mopidy.utils.network.has_ipv6', False)
    def test_format_hostname_does_nothing_when_only_ipv4_available(self):
        network.has_ipv6 = False
        self.assertEquals(network.format_hostname('0.0.0.0'), '0.0.0.0')


class TryIPv6SocketTest(unittest.TestCase):
    @patch('socket.has_ipv6', False)
    def test_system_that_claims_no_ipv6_support(self):
        self.assertFalse(network._try_ipv6_socket())

    @patch('socket.has_ipv6', True)
    @patch('socket.socket')
    def test_system_with_broken_ipv6(self, socket_mock):
        socket_mock.side_effect = IOError()
        self.assertFalse(network._try_ipv6_socket())

    @patch('socket.has_ipv6', True)
    @patch('socket.socket')
    def test_with_working_ipv6(self, socket_mock):
        socket_mock.return_value = Mock()
        self.assertTrue(network._try_ipv6_socket())


class CreateSocketTest(unittest.TestCase):
    @patch('mopidy.utils.network.has_ipv6', False)
    @patch('socket.socket')
    def test_ipv4_socket(self, socket_mock):
        network.create_socket()
        self.assertEqual(socket_mock.call_args[0],
            (socket.AF_INET, socket.SOCK_STREAM))

    @patch('mopidy.utils.network.has_ipv6', True)
    @patch('socket.socket')
    def test_ipv6_socket(self, socket_mock):
        network.create_socket()
        self.assertEqual(socket_mock.call_args[0],
            (socket.AF_INET6, socket.SOCK_STREAM))

    @SkipTest
    def test_ipv6_only_is_set(self):
        pass

class ServerTest(unittest.TestCase):
    def setUp(self):
        self.protocol = network.LineProtocol
        self.addr = (sentinel.host, sentinel.port)
        self.host, self.port = self.addr

        self.create_server_socket_patchter = patch.object(
            network.Server, 'create_server_socket', new=Mock())
        self.register_server_socket_patcher = patch.object(
            network.Server, 'register_server_socket', new=Mock())

        self.create_server_socket_patchter.start()
        self.register_server_socket_patcher.start()

    def tearDown(self):
        self.create_server_socket_patchter.stop()
        self.register_server_socket_patcher.stop()

    def create_server(self):
        return network.Server(sentinel.host, sentinel.port, self.protocol)

    def test_init_creates_socket_and_registers_it(self):
        server = self.create_server()
        sock = server.create_server_socket.return_value
        fileno = sock.fileno.return_value

        server.create_server_socket.assert_called_once_with(self.host, self.port)
        server.register_server_socket.assert_called_once_with(fileno)

    @patch.object(network, 'create_socket', spec=socket.SocketType)
    def test_create_server_socket_sets_up_listener(self, create_socket):
        self.create_server_socket_patchter.stop()

        try:
            server = self.create_server()
            sock = create_socket.return_value

            sock.setblocking.assert_called_once_with(False)
            sock.bind.assert_called_once_with(self.addr)
            self.assertEqual(1, sock.listen.call_count)
            self.assertEqual(sock, server.server_socket)
        finally:
            self.create_server_socket_patchter.start()

    @SkipTest
    def test_create_server_socket_fails(self):
        # FIXME define what should happen in this case, let the error propegate
        # or do something else?
        pass

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_register_server_socket_sets_up_io_watch(self):
        self.register_server_socket_patcher.stop()

        try:
            server = self.create_server()
            sock = server.create_server_socket.return_value
            fileno = sock.fileno.return_value

            gobject.io_add_watch.assert_called_once_with(
                fileno, gobject.IO_IN, server.handle_connection)
        finally:
            self.register_server_socket_patcher.start()

    @patch.object(network.Server, 'accept_connection', new=Mock())
    @patch.object(network.Server, 'maximum_connections_exceeded', new=Mock())
    @patch.object(network.Server, 'reject_connection', new=Mock())
    @patch.object(network.Server, 'init_connection', new=Mock())
    def test_handle_connection(self):
        server = self.create_server()
        server.accept_connection.return_value = (sentinel.sock, self.addr)
        server.maximum_connections_exceeded.return_value = False

        server.handle_connection(sentinel.fileno, gobject.IO_IN)

        server.accept_connection.assert_called_once_with()
        server.maximum_connections_exceeded.assert_called_once_with()
        server.init_connection.assert_called_once_with(sentinel.sock, self.addr)
        self.assertEquals(0, server.reject_connection.call_count)

    @patch.object(network.Server, 'accept_connection', new=Mock())
    @patch.object(network.Server, 'maximum_connections_exceeded', new=Mock())
    @patch.object(network.Server, 'reject_connection', new=Mock())
    @patch.object(network.Server, 'init_connection', new=Mock())
    def test_handle_connection_exceeded_connections(self):
        server = self.create_server()
        server.accept_connection.return_value = (sentinel.sock, self.addr)
        server.maximum_connections_exceeded.return_value = True

        server.handle_connection(sentinel.fileno, gobject.IO_IN)

        server.accept_connection.assert_called_once_with()
        server.maximum_connections_exceeded.assert_called_once_with()
        server.reject_connection.assert_called_once_with(sentinel.sock, self.addr)
        self.assertEquals(0, server.init_connection.call_count)

    def test_accept_connection(self):
        server = self.create_server()
        sock = server.create_server_socket.return_value
        sock.accept.return_value = (sentinel.sock, self.addr)

        self.assertEquals((sentinel.sock, self.addr), server.accept_connection())

    def test_accept_connection_recoverable_error(self):
        server = self.create_server()
        sock = server.create_server_socket.return_value

        sock.accept.side_effect = socket.error(errno.EAGAIN, '')
        self.assertRaises(network.ShouldRetrySocketCall, server.accept_connection)

        sock.accept.side_effect = socket.error(errno.EINTR, '')
        self.assertRaises(network.ShouldRetrySocketCall, server.accept_connection)

    def test_accept_connection_recoverable_error(self):
        server = self.create_server()
        sock = server.create_server_socket.return_value

        sock.accept.side_effect = socket.error()
        self.assertRaises(socket.error, server.accept_connection)

    @patch.object(network.Server, 'number_of_connections', new=Mock())
    def test_maximum_connections_exceeded(self):
        server = self.create_server()
        maximum_connections = server.max_connections

        server.number_of_connections.return_value = maximum_connections + 1
        self.assertTrue(server.maximum_connections_exceeded())

        server.number_of_connections.return_value = maximum_connections
        self.assertTrue(server.maximum_connections_exceeded())

        server.number_of_connections.return_value = maximum_connections - 1
        self.assertFalse(server.maximum_connections_exceeded())

    @patch('pykka.registry.ActorRegistry.get_by_class')
    def test_number_of_connections(self, get_by_class):
        server = self.create_server()

        get_by_class.return_value = [1, 2, 3]
        self.assertEqual(3, server.number_of_connections())

        get_by_class.return_value = []
        self.assertEqual(0, server.number_of_connections())

    @patch.object(network, 'Connection', new=Mock())
    def test_init_connection(self):
        server = self.create_server()
        server.init_connection(sentinel.sock, self.addr)

        network.Connection.assert_called_once_with(server.protocol, sentinel.sock, self.addr, server.timeout)
