#encoding: utf-8

import errno
import gobject
import logging
import pykka
import socket
import unittest

from mopidy.utils import network

from mock import patch, sentinel, Mock
from tests import SkipTest, any_int, any_unicode

class FormatHostnameTest(unittest.TestCase):
    @patch('mopidy.utils.network.has_ipv6', True)
    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        network.has_ipv6 = True
        self.assertEqual(network.format_hostname('0.0.0.0'), '::ffff:0.0.0.0')
        self.assertEqual(network.format_hostname('1.0.0.1'), '::ffff:1.0.0.1')

    @patch('mopidy.utils.network.has_ipv6', False)
    def test_format_hostname_does_nothing_when_only_ipv4_available(self):
        network.has_ipv6 = False
        self.assertEqual(network.format_hostname('0.0.0.0'), '0.0.0.0')


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
        self.mock.register_server_socket.assert_called_once_with(
            sentinel.fileno)

    @SkipTest
    def test_init_fails_on_fileno_call(self):
        sock = Mock(spec=socket.SocketType)
        sock.fileno.side_effect = socket.error
        self.mock.create_server_socket.return_value = sock

        network.Server.__init__(self.mock, sentinel.host,
            sentinel.port, sentinel.protocol)

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

    @SkipTest  # FIXME decide behaviour
    @patch.object(network, 'create_socket')
    def test_create_server_socket_fails(self):
        network.create_socket.side_effect = socket.error
        network.Server.create_server_socket(self.mock,
            sentinel.host, sentinel.port)

    @SkipTest  # FIXME decide behaviour
    @patch.object(network, 'create_socket', spec=socket.SocketType)
    def test_create_server_bind_fails(self):
        sock = create_socket.return_value
        sock.bind.side_effect = socket.error

        network.Server.create_server_socket(self.mock,
            sentinel.host, sentinel.port)

    @SkipTest  # FIXME decide behaviour
    @patch.object(network, 'create_socket', spec=socket.SocketType)
    def test_create_server_listen_fails(self):
        sock = create_socket.return_value
        sock.listen.side_effect = socket.error

        network.Server.create_server_socket(self.mock,
            sentinel.host, sentinel.port)

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
        addr = (sentinel.host, sentinel.port)
        protocol = Mock(spec=network.LineProtocol)
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(
            self.mock, protocol, sock, addr, sentinel.timeout)
        self.assertEqual(sock, self.mock.sock)
        self.assertEqual(protocol, self.mock.protocol)
        self.assertEqual(sentinel.timeout, self.mock.timeout)
        self.assertEqual(sentinel.host, self.mock.host)
        self.assertEqual(sentinel.port, self.mock.port)

    def test_init_handles_ipv6_addr(self):
        addr = (sentinel.host, sentinel.port,
            sentinel.flowinfo, sentinel.scopeid)
        protocol = Mock(spec=network.LineProtocol)
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(
            self.mock, protocol, sock, addr, sentinel.timeout)
        self.assertEqual(sentinel.host, self.mock.host)
        self.assertEqual(sentinel.port, self.mock.port)

    def test_stop_disables_recv_send_and_timeout(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.disable_timeout.assert_called_once_with()
        self.mock.disable_recv.assert_called_once_with()
        self.mock.disable_send.assert_called_once_with()

    def test_stop_closes_socket(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.sock.close.assert_called_once_with()

    def test_stop_closes_socket_error(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.close.side_effect = socket.error

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.sock.close.assert_called_once_with()

    def test_stop_stops_actor(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.actor_ref.stop.assert_called_once_with()

    def test_stop_handles_actor_already_being_stopped(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.actor_ref.stop.side_effect = pykka.ActorDeadError()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.actor_ref.stop.assert_called_once_with()

    def test_stop_sets_stopping_to_true(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.assertEqual(True, self.mock.stopping)

    def test_stop_does_not_proceed_when_already_stopping(self):
        self.mock.stopping = True
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.assertEqual(0, self.mock.actor_ref.stop.call_count)
        self.assertEqual(0, self.mock.sock.close.call_count)

    @patch.object(network.logger, 'log', new=Mock())
    def test_stop_logs_reason(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        network.logger.log.assert_called_once_with(
            logging.DEBUG, sentinel.reason)

    @patch.object(network.logger, 'log', new=Mock())
    def test_stop_logs_reason_with_level(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason,
            level=sentinel.level)
        network.logger.log.assert_called_once_with(
            sentinel.level, sentinel.reason)

    @patch.object(network.logger, 'log', new=Mock())
    def test_stop_logs_that_it_is_calling_itself(self):
        self.mock.stopping = True
        self.mock.actor_ref = Mock()
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        network.logger.log(any_int, any_unicode)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_recv_registers_with_gobject(self):
        self.mock.recv_id = None
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.fileno.return_value = sentinel.fileno
        gobject.io_add_watch.return_value = sentinel.tag

        network.Connection.enable_recv(self.mock)
        gobject.io_add_watch.assert_called_once_with(sentinel.fileno,
            gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP,
            self.mock.recv_callback)
        self.assertEqual(sentinel.tag, self.mock.recv_id)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_recv_already_registered(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.recv_id = sentinel.tag

        network.Connection.enable_recv(self.mock)
        self.assertEqual(0, gobject.io_add_watch.call_count)

    def test_enable_recv_does_not_change_tag(self):
        self.mock.recv_id = sentinel.tag
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.enable_recv(self.mock)
        self.assertEqual(sentinel.tag, self.mock.recv_id)

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

    def test_enable_recv_on_closed_socket(self):
        self.mock.recv_id = None
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.fileno.side_effect = socket.error(errno.EBADF, '')

        network.Connection.enable_recv(self.mock)
        self.mock.stop.assert_called_once_with(any_unicode)
        self.assertEqual(None, self.mock.recv_id)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_send_registers_with_gobject(self):
        self.mock.send_id = None
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.fileno.return_value = sentinel.fileno
        gobject.io_add_watch.return_value = sentinel.tag

        network.Connection.enable_send(self.mock)
        gobject.io_add_watch.assert_called_once_with(sentinel.fileno,
            gobject.IO_OUT | gobject.IO_ERR | gobject.IO_HUP,
            self.mock.send_callback)
        self.assertEqual(sentinel.tag, self.mock.send_id)

    @patch.object(gobject, 'io_add_watch', new=Mock())
    def test_enable_send_already_registered(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.send_id = sentinel.tag

        network.Connection.enable_send(self.mock)
        self.assertEqual(0, gobject.io_add_watch.call_count)

    def test_enable_send_does_not_change_tag(self):
        self.mock.send_id = sentinel.tag
        self.mock.sock = Mock(spec=socket.SocketType)

        network.Connection.enable_send(self.mock)
        self.assertEqual(sentinel.tag, self.mock.send_id)

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

    def test_enable_send_on_closed_socket(self):
        self.mock.send_id = None
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.fileno.side_effect = socket.error(errno.EBADF, '')

        network.Connection.enable_send(self.mock)
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

    def test_enable_timeout_does_not_call_disable_for_invalid_timeout(self):
        self.mock.timeout = 0
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, self.mock.disable_timeout.call_count)

        self.mock.timeout = -1
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, self.mock.disable_timeout.call_count)

        self.mock.timeout = None
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, self.mock.disable_timeout.call_count)

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

    def test_send_acquires_and_releases_lock(self):
        self.mock.send_lock = Mock()
        self.mock.send_buffer = ''

        network.Connection.send(self.mock, 'data')
        self.mock.send_lock.acquire.assert_called_once_with(True)
        self.mock.send_lock.release.assert_called_once_with()

    def test_send_appends_to_send_buffer(self):
        self.mock.send_lock = Mock()
        self.mock.send_buffer = ''

        network.Connection.send(self.mock, 'abc')
        self.assertEqual('abc', self.mock.send_buffer)

        network.Connection.send(self.mock, 'def')
        self.assertEqual('abcdef', self.mock.send_buffer)

        network.Connection.send(self.mock, '')
        self.assertEqual('abcdef', self.mock.send_buffer)

    def test_send_calls_enable_send(self):
        self.mock.send_lock = Mock()
        self.mock.send_buffer = ''

        network.Connection.send(self.mock, 'data')
        self.mock.enable_send.assert_called_once_with()

    def test_recv_callback_respects_io_err(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(self.mock,
            sentinel.fd, gobject.IO_IN | gobject.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_respects_io_hup(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(self.mock,
            sentinel.fd, gobject.IO_IN | gobject.IO_HUP))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_respects_io_hup_and_io_err(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(self.mock,
            sentinel.fd, gobject.IO_IN | gobject.IO_HUP | gobject.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_sends_data_to_actor(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.recv.return_value = 'data'
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.actor_ref.send_one_way.assert_called_once_with(
            {'received': 'data'})

    def test_recv_callback_handles_dead_actors(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.recv.return_value = 'data'
        self.mock.actor_ref = Mock()
        self.mock.actor_ref.send_one_way.side_effect = pykka.ActorDeadError()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_gets_no_data(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.recv.return_value = ''
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_recoverable_error(self):
        self.mock.sock = Mock(spec=socket.SocketType)

        for error in (errno.EWOULDBLOCK, errno.EINTR):
            self.mock.sock.recv.side_effect = socket.error(error, '')
            self.assertTrue(network.Connection.recv_callback(
                self.mock, sentinel.fd, gobject.IO_IN))
            self.assertEqual(0, self.mock.stop.call_count)

    def test_recv_callback_unrecoverable_error(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.recv.side_effect = socket.error

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.stop.assert_called_once_with(any_unicode)

    @SkipTest  # FIXME decide behaviour
    def test_send_callback_respects_io_err(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.send_callback(self.mock,
            sentinel.fd, gobject.IO_IN | gobject.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    @SkipTest  # FIXME decide behaviour
    def test_send_callback_respects_io_hup(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.send_callback(self.mock,
            sentinel.fd, gobject.IO_IN | gobject.IO_HUP))
        self.mock.stop.assert_called_once_with(any_unicode)

    @SkipTest  # FIXME decide behaviour
    def test_send_callback_respects_io_hup_and_io_err(self):
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.send_callback(self.mock,
            sentinel.fd, gobject.IO_IN | gobject.IO_HUP | gobject.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_send_callback_acquires_and_releases_lock(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = ''
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.send.return_value = 0

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.send_lock.acquire.assert_called_once_with(False)
        self.mock.send_lock.release.assert_called_once_with()

    def test_send_callback_fails_to_acquire_lock(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = False
        self.mock.send_buffer = ''
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.send.return_value = 0

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.send_lock.acquire.assert_called_once_with(False)
        self.assertEqual(0, self.mock.sock.send.call_count)

    def test_send_callback_sends_all_data(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = 'data'
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.send.return_value = 4

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.disable_send.assert_called_once_with()
        self.mock.sock.send.assert_called_once_with('data')
        self.assertEqual('', self.mock.send_buffer)

    def test_send_callback_sends_partial_data(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = 'data'
        self.mock.sock = Mock(spec=socket.SocketType)
        self.mock.sock.send.return_value = 2

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.sock.send.assert_called_once_with('data')
        self.assertEqual('ta', self.mock.send_buffer)

    def test_send_callback_recoverable_error(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = 'data'
        self.mock.sock = Mock(spec=socket.SocketType)

        for error in (errno.EWOULDBLOCK, errno.EINTR):
            self.mock.sock.send.side_effect = socket.error(error, '')
            self.assertTrue(network.Connection.send_callback(
                self.mock, sentinel.fd, gobject.IO_IN))
            self.assertEqual(0, self.mock.stop.call_count)

    def test_send_callback_unrecoverable_error(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = 'data'
        self.mock.sock = Mock(spec=socket.SocketType)

        self.mock.sock.send.side_effect = socket.error
        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, gobject.IO_IN))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_timeout_callback(self):
        self.mock.timeout = 10

        self.assertFalse(network.Connection.timeout_callback(self.mock))
        self.mock.stop.assert_called_once_with(any_unicode)


class LineProtocolTest(unittest.TestCase):
    def setUp(self):
        self.mock = Mock(spec=network.LineProtocol)
        self.mock.terminator = network.LineProtocol.terminator
        self.mock.encoding = network.LineProtocol.encoding

    def test_init_stores_values_in_attributes(self):
        network.LineProtocol.__init__(self.mock, sentinel.connection)
        self.assertEqual(sentinel.connection, self.mock.connection)
        self.assertEqual('', self.mock.recv_buffer)

    def test_on_receive_no_new_lines_adds_to_recv_buffer(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []

        network.LineProtocol.on_receive(self.mock, {'received': 'data'})
        self.assertEqual('data', self.mock.recv_buffer)
        self.mock.parse_lines.assert_called_once_with()
        self.assertEqual(0, self.mock.on_line_received.call_count)

    def test_on_receive_no_new_lines_toggles_timeout(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = []

        network.LineProtocol.on_receive(self.mock, {'received': 'data'})
        self.mock.connection.disable_timeout.assert_called_once_with()
        self.mock.connection.enable_timeout.assert_called_once_with()

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

    def test_on_receive_with_new_lines_calls_on_recieve(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.recv_buffer = ''
        self.mock.parse_lines.return_value = ['line1', 'line2']
        self.mock.decode.return_value = sentinel.decoded

        network.LineProtocol.on_receive(self.mock,
            {'received': 'line1\nline2\n'})
        self.assertEqual(2, self.mock.on_line_received.call_count)

    def test_parse_lines_emtpy_buffer(self):
        self.mock.recv_buffer = ''

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertRaises(StopIteration, lines.next)

    def test_parse_lines_no_terminator(self):
        self.mock.recv_buffer = 'data'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertRaises(StopIteration, lines.next)

    def test_parse_lines_termintor(self):
        self.mock.recv_buffer = 'data\n'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data', lines.next())
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_no_data_before_terminator(self):
        self.mock.recv_buffer = '\n'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('', lines.next())
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_extra_data_after_terminator(self):
        self.mock.recv_buffer = 'data1\ndata2'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data1', lines.next())
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('data2', self.mock.recv_buffer)

    def test_parse_lines_unicode(self):
        self.mock.recv_buffer = u'æøå\n'.encode('utf-8')

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual(u'æøå'.encode('utf-8'), lines.next())
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('', self.mock.recv_buffer)

    def test_parse_lines_multiple_lines(self):
        self.mock.recv_buffer = 'abc\ndef\nghi\njkl'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('abc', lines.next())
        self.assertEqual('def', lines.next())
        self.assertEqual('ghi', lines.next())
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('jkl', self.mock.recv_buffer)

    def test_parse_lines_multiple_calls(self):
        self.mock.recv_buffer = 'data'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('data', self.mock.recv_buffer)
        self.mock.recv_buffer += '\n'

        lines = network.LineProtocol.parse_lines(self.mock)
        self.assertEqual('data', lines.next())
        self.assertRaises(StopIteration, lines.next)
        self.assertEqual('', self.mock.recv_buffer)

    def test_send_lines_called_with_no_lines(self):
        self.mock.connection = Mock(spec=network.Connection)

        network.LineProtocol.send_lines(self.mock, [])
        self.assertEqual(0, self.mock.encode.call_count)
        self.assertEqual(0, self.mock.connection.send.call_count)

    def test_send_lines_calls_join_lines(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = 'lines'

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.join_lines.assert_called_once_with(sentinel.lines)

    def test_send_line_encodes_joined_lines_with_final_terminator(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = u'lines\n'

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.encode.assert_called_once_with(u'lines\n')

    def test_send_lines_sends_encoded_string(self):
        self.mock.connection = Mock(spec=network.Connection)
        self.mock.join_lines.return_value = 'lines'
        self.mock.encode.return_value = sentinel.data

        network.LineProtocol.send_lines(self.mock, sentinel.lines)
        self.mock.connection.send.assert_called_once_with(sentinel.data)

    def test_join_lines_returns_empty_string_for_no_lines(self):
        self.assertEqual(u'', network.LineProtocol.join_lines(self.mock, []))

    def test_join_lines_returns_joined_lines(self):
        self.assertEqual(u'1\n2\n', network.LineProtocol.join_lines(
            self.mock, [u'1', u'2']))

    def test_decode_calls_decode_on_string(self):
        string = Mock()

        network.LineProtocol.decode(self.mock, string)
        string.decode.assert_called_once_with(self.mock.encoding)

    def test_decode_plain_ascii(self):
        self.assertEqual(u'abc', network.LineProtocol.decode(self.mock, 'abc'))

    def test_decode_utf8(self):
        self.assertEqual(u'æøå', network.LineProtocol.decode(
            self.mock, u'æøå'.encode('utf-8')))

    @SkipTest  # FIXME decide behaviour
    def test_decode_invalid_data(self):
        string = Mock()
        string.decode.side_effect = UnicodeError

        network.LineProtocol.decode(self.mock, string)

    def test_encode_calls_encode_on_string(self):
        string = Mock()

        network.LineProtocol.encode(self.mock, string)
        string.encode.assert_called_once_with(self.mock.encoding)

    def test_encode_plain_ascii(self):
        self.assertEqual('abc', network.LineProtocol.encode(self.mock, u'abc'))

    def test_encode_utf8(self):
        self.assertEqual(u'æøå'.encode('utf-8'),
            network.LineProtocol.encode(self.mock, u'æøå'))

    @SkipTest  # FIXME decide behaviour
    def test_encode_invalid_data(self):
        string = Mock()
        string.encode.side_effect = UnicodeError

        network.LineProtocol.encode(self.mock, string)

    @SkipTest
    def test_host_property(self):
        pass

    @SkipTest
    def test_port_property(self):
        pass
