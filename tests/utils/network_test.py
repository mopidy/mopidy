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
        self.assertFalse(network.try_ipv6_socket())

    @patch('socket.has_ipv6', True)
    @patch('socket.socket')
    def test_system_with_broken_ipv6(self, socket_mock):
        socket_mock.side_effect = IOError()
        self.assertFalse(network.try_ipv6_socket())

    @patch('socket.has_ipv6', True)
    @patch('socket.socket')
    def test_with_working_ipv6(self, socket_mock):
        socket_mock.return_value = Mock()
        self.assertTrue(network.try_ipv6_socket())


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
        self.mock.register_server_socket.assert_called_once_with(sentinel.fileno)

    def test_init_stores_values_in_attributes(self):
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
        self.assertEqual(1, sock.listen.call_count)

    @SkipTest
    def test_create_server_socket_fails(self):
        # FIXME define what should happen in this case, let the error propegate
        # or do something else?
        pass

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_register_server_socket_sets_up_io_watch(self):
        network.Server.register_server_socket(self.mock, sentinel.fileno)
        gobject.io_add_watch.assert_called_once_with(sentinel.fileno,
            gobject.IO_IN, self.mock.handle_connection)

    def test_handle_connection(self):
        self.mock.accept_connection.return_value = (sentinel.sock, sentinel.addr)
        self.mock.maximum_connections_exceeded.return_value = False

        network.Server.handle_connection(self.mock, sentinel.fileno, gobject.IO_IN)
        self.mock.accept_connection.assert_called_once_with()
        self.mock.maximum_connections_exceeded.assert_called_once_with()
        self.mock.init_connection.assert_called_once_with(sentinel.sock, sentinel.addr)
        self.assertEquals(0, self.mock.reject_connection.call_count)

    def test_handle_connection_exceeded_connections(self):
        self.mock.accept_connection.return_value = (sentinel.sock, sentinel.addr)
        self.mock.maximum_connections_exceeded.return_value = True

        network.Server.handle_connection(self.mock, sentinel.fileno, gobject.IO_IN)
        self.mock.accept_connection.assert_called_once_with()
        self.mock.maximum_connections_exceeded.assert_called_once_with()
        self.mock.reject_connection.assert_called_once_with(sentinel.sock, sentinel.addr)
        self.assertEquals(0, self.mock.init_connection.call_count)

    def test_accept_connection(self):
        sock = Mock(spec=socket.SocketType)
        sock.accept.return_value = (sentinel.sock, sentinel.addr)
        self.mock.server_socket = sock

        sock, addr = network.Server.accept_connection(self.mock)
        self.assertEquals(sentinel.sock, sock)
        self.assertEquals(sentinel.addr, addr)

    def test_accept_connection_recoverable_error(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.server_socket = sock

        sock.accept.side_effect = socket.error(errno.EAGAIN, '')
        self.assertRaises(network.ShouldRetrySocketCall,
            network.Server.accept_connection, self.mock)

        sock.accept.side_effect = socket.error(errno.EINTR, '')
        self.assertRaises(network.ShouldRetrySocketCall,
            network.Server.accept_connection, self.mock)

    def test_accept_connection_unrecoverable_error(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.server_socket = sock

        sock.accept.side_effect = socket.error()
        self.assertRaises(socket.error,
            network.Server.accept_connection, self.mock)

    @patch.object(network.Server, 'number_of_connections', new=Mock())
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
        sock.close.side_effect = socket.error()

        network.Server.reject_connection(self.mock, sock,
            (sentinel.host, sentinel.port))
        sock.close.assert_called_once_with()

class ConnectionTest(unittest.TestCase):
    def setUp(self):
        self.mock = Mock(spec=network.Connection)

    def test_init_ensure_nonblocking_io(self):
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(self.mock, Mock(), sock,
            (sentinel.host, sentinel.port), sentinel.timeout)
        sock.setblocking.assert_called_once_with(False)

    def test_init_starts_actor(self):
        protocol = Mock(spec=network.LineProtocol)

        network.Connection.__init__(self.mock, protocol, Mock(),
            (sentinel.host, sentinel.port), sentinel.timeout)
        protocol.start.assert_called_once_with(self.mock)

    def test_init_enables_recv_and_timeout(self):
        network.Connection.__init__(self.mock, Mock(), Mock(),
            (sentinel.host, sentinel.port), sentinel.timeout)
        self.mock.enable_recv.assert_called_once_with()
        self.mock.enable_timeout.assert_called_once_with()

    def test_init_stores_values_in_attributes(self):
        protocol = Mock(spec=network.LineProtocol)
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(self.mock, protocol, sock,
            (sentinel.host, sentinel.port), sentinel.timeout)
        self.assertEqual(sock, self.mock.sock)
        self.assertEqual(protocol, self.mock.protocol)
        self.assertEqual(sentinel.timeout, self.mock.timeout)
        self.assertEqual(sentinel.host, self.mock.host)
        self.assertEqual(sentinel.port, self.mock.port)

    def test_stop_disables_recv_send_and_timeout(self):
        network.Connection.stop(self.mock)
        self.mock.disable_timeout.assert_called_once_with()
        self.mock.disable_recv.assert_called_once_with()
        self.mock.disable_timeout.assert_called_once_with()

    def test_stop_closes_socket(self):
        sock = Mock(spec=socket.SocketType)
        self.mock.sock = sock

        network.Connection.stop(self.mock)
        sock.close.assert_called_once_with()

    def test_stop_closes_socket_error(self):
        sock = Mock(spec=socket.SocketType)
        sock.close.side_effect = socket.error()
        self.mock.sock = sock

        network.Connection.stop(self.mock)
        sock.close.assert_called_once_with()

    def test_stop_return_false(self):
        self.assertFalse(network.Connection.stop(self.mock))

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_recv_registers_with_gobject(self):
        self.mock.recv_id = None
        self.mock.sock.fileno.return_value = sentinel.fileno
        gobject.io_add_watch.return_value = sentinel.tag

        network.Connection.enable_recv(self.mock)
        gobject.io_add_watch.assert_called_once_with(sentinel.fileno,
            gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP,
            self.mock.recv_callback)
        self.assertEqual(sentinel.tag, self.mock.recv_id)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_recv_already_registered(self):
        self.mock.recv_id = sentinel.tag

        network.Connection.enable_recv(self.mock)
        self.assertEqual(0, gobject.io_add_watch.call_count)

    @patch.object(gobject, 'source_remove', new=Mock())
    def test_disable_recv_deregisters(self):
        self.mock.recv_id = sentinel.tag

        network.Connection.disable_recv(self.mock)
        gobject.source_remove.assert_called_once_with(sentinel.tag)
        self.assertEqual(None, self.mock.recv_id)

    @patch.object(gobject, 'source_remove', new=Mock())
    def test_disable_recv_already_deregistered(self):
        self.mock.recv_id = None

        network.Connection.disable_recv(self.mock)
        self.assertEqual(0, gobject.source_remove.call_count)
        self.assertEqual(None, self.mock.recv_id)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_send_registers_with_gobject(self):
        self.mock.send_id = None
        self.mock.sock.fileno.return_value = sentinel.fileno
        gobject.io_add_watch.return_value = sentinel.tag

        network.Connection.enable_send(self.mock)
        gobject.io_add_watch.assert_called_once_with(sentinel.fileno,
            gobject.IO_OUT | gobject.IO_ERR | gobject.IO_HUP,
            self.mock.send_callback)
        self.assertEqual(sentinel.tag, self.mock.send_id)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_send_already_registered(self):
        self.mock.send_id = sentinel.tag

        network.Connection.enable_send(self.mock)
        self.assertEqual(0, gobject.io_add_watch.call_count)

    @patch.object(gobject, 'source_remove', new=Mock())
    def test_disable_send_deregisters(self):
        self.mock.send_id = sentinel.tag

        network.Connection.disable_send(self.mock)
        gobject.source_remove.assert_called_once_with(sentinel.tag)
        self.assertEqual(None, self.mock.send_id)

    @patch.object(gobject, 'source_remove', new=Mock())
    def test_disable_send_already_deregistered(self):
        self.mock.send_id = None

        network.Connection.disable_send(self.mock)
        self.assertEqual(0, gobject.source_remove.call_count)
        self.assertEqual(None, self.mock.send_id)

    @patch.object(gobject, 'timeout_add_seconds', new=Mock())
    def test_enable_timeout_clears_existing_timeouts(self):
        self.mock.timeout = 10

        network.Connection.enable_timeout(self.mock)
        self.mock.disable_timeout.assert_called_once_with()

    @patch.object(gobject, 'timeout_add_seconds', new=Mock())
    def test_enable_timeout_add_gobject_timeout(self):
        self.mock.timeout = 10
        gobject.timeout_add_seconds.return_value = sentinel.tag

        network.Connection.enable_timeout(self.mock)
        gobject.timeout_add_seconds.assert_called_once_with(10,
            self.mock.timeout_callback)
        self.assertEqual(sentinel.tag, self.mock.timeout_id)

    @patch.object(gobject, 'timeout_add_seconds', new=Mock())
    def test_enable_timeout_does_not_add_timeout(self):
        self.mock.timeout = 0
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, gobject.timeout_add_seconds.call_count)

        self.mock.timeout = -1
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, gobject.timeout_add_seconds.call_count)

        self.mock.timeout = None
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, gobject.timeout_add_seconds.call_count)

    @patch.object(gobject, 'source_remove', new=Mock())
    def test_disable_timeout_deregisters(self):
        self.mock.timeout_id = sentinel.tag

        network.Connection.disable_timeout(self.mock)
        gobject.source_remove.assert_called_once_with(sentinel.tag)
        self.assertEqual(None, self.mock.timeout_id)

    @patch.object(gobject, 'source_remove', new=Mock())
    def test_disable_timeout_already_deregistered(self):
        self.mock.timeout_id = None

        network.Connection.disable_timeout(self.mock)
        self.assertEqual(0, gobject.source_remove.call_count)
        self.assertEqual(None, self.mock.timeout_id)

    @SkipTest
    def test_recv_callback(self):
        pass

    @SkipTest
    def test_send_callback(self):
        pass

    @SkipTest
    def test_timeout_callback(self):
        pass
