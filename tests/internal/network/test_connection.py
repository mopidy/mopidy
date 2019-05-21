from __future__ import absolute_import, unicode_literals

import errno
import logging
import socket
import unittest

from mock import Mock, call, patch, sentinel

import pykka

from mopidy.internal import network
from mopidy.internal.gi import GLib

from tests import any_int, any_unicode


class ConnectionTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.mock = Mock(spec=network.Connection)

    def test_init_ensure_nonblocking_io(self):
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(
            self.mock, Mock(), {}, sock, (sentinel.host, sentinel.port),
            sentinel.timeout)
        sock.setblocking.assert_called_once_with(False)

    def test_init_starts_actor(self):
        protocol = Mock(spec=network.LineProtocol)

        network.Connection.__init__(
            self.mock, protocol, {}, Mock(), (sentinel.host, sentinel.port),
            sentinel.timeout)
        protocol.start.assert_called_once_with(self.mock)

    def test_init_enables_recv_and_timeout(self):
        network.Connection.__init__(
            self.mock, Mock(), {}, Mock(), (sentinel.host, sentinel.port),
            sentinel.timeout)
        self.mock.enable_recv.assert_called_once_with()
        self.mock.enable_timeout.assert_called_once_with()

    def test_init_stores_values_in_attributes(self):
        addr = (sentinel.host, sentinel.port)
        protocol = Mock(spec=network.LineProtocol)
        protocol_kwargs = {}
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(
            self.mock, protocol, protocol_kwargs, sock, addr, sentinel.timeout)
        self.assertEqual(sock, self.mock._sock)
        self.assertEqual(protocol, self.mock.protocol)
        self.assertEqual(protocol_kwargs, self.mock.protocol_kwargs)
        self.assertEqual(sentinel.timeout, self.mock.timeout)
        self.assertEqual(sentinel.host, self.mock.host)
        self.assertEqual(sentinel.port, self.mock.port)

    def test_init_handles_ipv6_addr(self):
        addr = (
            sentinel.host, sentinel.port, sentinel.flowinfo, sentinel.scopeid)
        protocol = Mock(spec=network.LineProtocol)
        protocol_kwargs = {}
        sock = Mock(spec=socket.SocketType)

        network.Connection.__init__(
            self.mock, protocol, protocol_kwargs, sock, addr, sentinel.timeout)
        self.assertEqual(sentinel.host, self.mock.host)
        self.assertEqual(sentinel.port, self.mock.port)

    def test_stop_disables_recv_send_and_timeout(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.disable_timeout.assert_called_once_with()
        self.mock.disable_recv.assert_called_once_with()
        self.mock.disable_send.assert_called_once_with()

    def test_stop_closes_socket(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock._sock.close.assert_called_once_with()

    def test_stop_closes_socket_error(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.close.side_effect = socket.error

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock._sock.close.assert_called_once_with()

    def test_stop_stops_actor(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.actor_ref.stop.assert_called_once_with(block=False)

    def test_stop_handles_actor_already_being_stopped(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock.actor_ref.stop.side_effect = pykka.ActorDeadError()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.mock.actor_ref.stop.assert_called_once_with(block=False)

    def test_stop_sets_stopping_to_true(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.assertEqual(True, self.mock.stopping)

    def test_stop_does_not_proceed_when_already_stopping(self):
        self.mock.stopping = True
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        self.assertEqual(0, self.mock.actor_ref.stop.call_count)
        self.assertEqual(0, self.mock._sock.close.call_count)

    @patch.object(network.logger, 'log', new=Mock())
    def test_stop_logs_reason(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        network.logger.log.assert_called_once_with(
            logging.DEBUG, sentinel.reason)

    @patch.object(network.logger, 'log', new=Mock())
    def test_stop_logs_reason_with_level(self):
        self.mock.stopping = False
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(
            self.mock, sentinel.reason, level=sentinel.level)
        network.logger.log.assert_called_once_with(
            sentinel.level, sentinel.reason)

    @patch.object(network.logger, 'log', new=Mock())
    def test_stop_logs_that_it_is_calling_itself(self):
        self.mock.stopping = True
        self.mock.actor_ref = Mock()
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.stop(self.mock, sentinel.reason)
        network.logger.log(any_int, any_unicode)

    @patch.object(GLib, 'io_add_watch', new=Mock())
    def test_enable_recv_registers_with_glib(self):
        self.mock.recv_id = None
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.fileno.return_value = sentinel.fileno
        GLib.io_add_watch.return_value = sentinel.tag

        network.Connection.enable_recv(self.mock)
        GLib.io_add_watch.assert_called_once_with(
            sentinel.fileno,
            GLib.IO_IN | GLib.IO_ERR | GLib.IO_HUP,
            self.mock.recv_callback)
        self.assertEqual(sentinel.tag, self.mock.recv_id)

    @patch.object(GLib, 'io_add_watch', new=Mock())
    def test_enable_recv_already_registered(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock.recv_id = sentinel.tag

        network.Connection.enable_recv(self.mock)
        self.assertEqual(0, GLib.io_add_watch.call_count)

    def test_enable_recv_does_not_change_tag(self):
        self.mock.recv_id = sentinel.tag
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.enable_recv(self.mock)
        self.assertEqual(sentinel.tag, self.mock.recv_id)

    @patch.object(GLib, 'source_remove', new=Mock())
    def test_disable_recv_deregisters(self):
        self.mock.recv_id = sentinel.tag

        network.Connection.disable_recv(self.mock)
        GLib.source_remove.assert_called_once_with(sentinel.tag)
        self.assertEqual(None, self.mock.recv_id)

    @patch.object(GLib, 'source_remove', new=Mock())
    def test_disable_recv_already_deregistered(self):
        self.mock.recv_id = None

        network.Connection.disable_recv(self.mock)
        self.assertEqual(0, GLib.source_remove.call_count)
        self.assertEqual(None, self.mock.recv_id)

    def test_enable_recv_on_closed_socket(self):
        self.mock.recv_id = None
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.fileno.side_effect = socket.error(errno.EBADF, '')

        network.Connection.enable_recv(self.mock)
        self.mock.stop.assert_called_once_with(any_unicode)
        self.assertEqual(None, self.mock.recv_id)

    @patch.object(GLib, 'io_add_watch', new=Mock())
    def test_enable_send_registers_with_glib(self):
        self.mock.send_id = None
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.fileno.return_value = sentinel.fileno
        GLib.io_add_watch.return_value = sentinel.tag

        network.Connection.enable_send(self.mock)
        GLib.io_add_watch.assert_called_once_with(
            sentinel.fileno,
            GLib.IO_OUT | GLib.IO_ERR | GLib.IO_HUP,
            self.mock.send_callback)
        self.assertEqual(sentinel.tag, self.mock.send_id)

    @patch.object(GLib, 'io_add_watch', new=Mock())
    def test_enable_send_already_registered(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock.send_id = sentinel.tag

        network.Connection.enable_send(self.mock)
        self.assertEqual(0, GLib.io_add_watch.call_count)

    def test_enable_send_does_not_change_tag(self):
        self.mock.send_id = sentinel.tag
        self.mock._sock = Mock(spec=socket.SocketType)

        network.Connection.enable_send(self.mock)
        self.assertEqual(sentinel.tag, self.mock.send_id)

    @patch.object(GLib, 'source_remove', new=Mock())
    def test_disable_send_deregisters(self):
        self.mock.send_id = sentinel.tag

        network.Connection.disable_send(self.mock)
        GLib.source_remove.assert_called_once_with(sentinel.tag)
        self.assertEqual(None, self.mock.send_id)

    @patch.object(GLib, 'source_remove', new=Mock())
    def test_disable_send_already_deregistered(self):
        self.mock.send_id = None

        network.Connection.disable_send(self.mock)
        self.assertEqual(0, GLib.source_remove.call_count)
        self.assertEqual(None, self.mock.send_id)

    def test_enable_send_on_closed_socket(self):
        self.mock.send_id = None
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.fileno.side_effect = socket.error(errno.EBADF, '')

        network.Connection.enable_send(self.mock)
        self.assertEqual(None, self.mock.send_id)

    @patch.object(GLib, 'timeout_add_seconds', new=Mock())
    def test_enable_timeout_clears_existing_timeouts(self):
        self.mock.timeout = 10

        network.Connection.enable_timeout(self.mock)
        self.mock.disable_timeout.assert_called_once_with()

    @patch.object(GLib, 'timeout_add_seconds', new=Mock())
    def test_enable_timeout_add_glib_timeout(self):
        self.mock.timeout = 10
        GLib.timeout_add_seconds.return_value = sentinel.tag

        network.Connection.enable_timeout(self.mock)
        GLib.timeout_add_seconds.assert_called_once_with(
            10, self.mock.timeout_callback)
        self.assertEqual(sentinel.tag, self.mock.timeout_id)

    @patch.object(GLib, 'timeout_add_seconds', new=Mock())
    def test_enable_timeout_does_not_add_timeout(self):
        self.mock.timeout = 0
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, GLib.timeout_add_seconds.call_count)

        self.mock.timeout = -1
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, GLib.timeout_add_seconds.call_count)

        self.mock.timeout = None
        network.Connection.enable_timeout(self.mock)
        self.assertEqual(0, GLib.timeout_add_seconds.call_count)

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

    @patch.object(GLib, 'source_remove', new=Mock())
    def test_disable_timeout_deregisters(self):
        self.mock.timeout_id = sentinel.tag

        network.Connection.disable_timeout(self.mock)
        GLib.source_remove.assert_called_once_with(sentinel.tag)
        self.assertEqual(None, self.mock.timeout_id)

    @patch.object(GLib, 'source_remove', new=Mock())
    def test_disable_timeout_already_deregistered(self):
        self.mock.timeout_id = None

        network.Connection.disable_timeout(self.mock)
        self.assertEqual(0, GLib.source_remove.call_count)
        self.assertEqual(None, self.mock.timeout_id)

    def test_queue_send_acquires_and_releases_lock(self):
        self.mock.send_lock = Mock()
        self.mock.send_buffer = ''

        network.Connection.queue_send(self.mock, 'data')
        self.mock.send_lock.acquire.assert_called_once_with(True)
        self.mock.send_lock.release.assert_called_once_with()

    def test_queue_send_calls_send(self):
        self.mock.send_buffer = ''
        self.mock.send_lock = Mock()
        self.mock.send.return_value = ''

        network.Connection.queue_send(self.mock, 'data')
        self.mock.send.assert_called_once_with('data')
        self.assertEqual(0, self.mock.enable_send.call_count)
        self.assertEqual('', self.mock.send_buffer)

    def test_queue_send_calls_enable_send_for_partial_send(self):
        self.mock.send_buffer = ''
        self.mock.send_lock = Mock()
        self.mock.send.return_value = 'ta'

        network.Connection.queue_send(self.mock, 'data')
        self.mock.send.assert_called_once_with('data')
        self.mock.enable_send.assert_called_once_with()
        self.assertEqual('ta', self.mock.send_buffer)

    def test_queue_send_calls_send_with_existing_buffer(self):
        self.mock.send_buffer = 'foo'
        self.mock.send_lock = Mock()
        self.mock.send.return_value = ''

        network.Connection.queue_send(self.mock, 'bar')
        self.mock.send.assert_called_once_with('foobar')
        self.assertEqual(0, self.mock.enable_send.call_count)
        self.assertEqual('', self.mock.send_buffer)

    def test_recv_callback_respects_io_err(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, GLib.IO_IN | GLib.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_respects_io_hup(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, GLib.IO_IN | GLib.IO_HUP))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_respects_io_hup_and_io_err(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd,
            GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_sends_data_to_actor(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.recv.return_value = 'data'
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.actor_ref.tell.assert_called_once_with(
            {'received': 'data'})

    def test_recv_callback_handles_dead_actors(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.recv.return_value = 'data'
        self.mock.actor_ref = Mock()
        self.mock.actor_ref.tell.side_effect = pykka.ActorDeadError()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_recv_callback_gets_no_data(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.recv.return_value = ''
        self.mock.actor_ref = Mock()

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.assertEqual(self.mock.mock_calls, [
            call._sock.recv(any_int),
            call.disable_recv(),
            call.actor_ref.tell({'close': True}),
        ])

    def test_recv_callback_recoverable_error(self):
        self.mock._sock = Mock(spec=socket.SocketType)

        for error in (errno.EWOULDBLOCK, errno.EINTR):
            self.mock._sock.recv.side_effect = socket.error(error, '')
            self.assertTrue(network.Connection.recv_callback(
                self.mock, sentinel.fd, GLib.IO_IN))
            self.assertEqual(0, self.mock.stop.call_count)

    def test_recv_callback_unrecoverable_error(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.recv.side_effect = socket.error

        self.assertTrue(network.Connection.recv_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_send_callback_respects_io_err(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 1
        self.mock.send_lock = Mock()
        self.mock.actor_ref = Mock()
        self.mock.send_buffer = ''

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, GLib.IO_IN | GLib.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_send_callback_respects_io_hup(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 1
        self.mock.send_lock = Mock()
        self.mock.actor_ref = Mock()
        self.mock.send_buffer = ''

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, GLib.IO_IN | GLib.IO_HUP))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_send_callback_respects_io_hup_and_io_err(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 1
        self.mock.send_lock = Mock()
        self.mock.actor_ref = Mock()
        self.mock.send_buffer = ''

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd,
            GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_send_callback_acquires_and_releases_lock(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = ''
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 0

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.send_lock.acquire.assert_called_once_with(False)
        self.mock.send_lock.release.assert_called_once_with()

    def test_send_callback_fails_to_acquire_lock(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = False
        self.mock.send_buffer = ''
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 0

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.send_lock.acquire.assert_called_once_with(False)
        self.assertEqual(0, self.mock._sock.send.call_count)

    def test_send_callback_sends_all_data(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = 'data'
        self.mock.send.return_value = ''

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.disable_send.assert_called_once_with()
        self.mock.send.assert_called_once_with('data')
        self.assertEqual('', self.mock.send_buffer)

    def test_send_callback_sends_partial_data(self):
        self.mock.send_lock = Mock()
        self.mock.send_lock.acquire.return_value = True
        self.mock.send_buffer = 'data'
        self.mock.send.return_value = 'ta'

        self.assertTrue(network.Connection.send_callback(
            self.mock, sentinel.fd, GLib.IO_IN))
        self.mock.send.assert_called_once_with('data')
        self.assertEqual('ta', self.mock.send_buffer)

    def test_send_recoverable_error(self):
        self.mock._sock = Mock(spec=socket.SocketType)

        for error in (errno.EWOULDBLOCK, errno.EINTR):
            self.mock._sock.send.side_effect = socket.error(error, '')

            network.Connection.send(self.mock, 'data')
            self.assertEqual(0, self.mock.stop.call_count)

    def test_send_calls_socket_send(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 4

        self.assertEqual('', network.Connection.send(self.mock, 'data'))
        self.mock._sock.send.assert_called_once_with('data')

    def test_send_calls_socket_send_partial_send(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.return_value = 2

        self.assertEqual('ta', network.Connection.send(self.mock, 'data'))
        self.mock._sock.send.assert_called_once_with('data')

    def test_send_unrecoverable_error(self):
        self.mock._sock = Mock(spec=socket.SocketType)
        self.mock._sock.send.side_effect = socket.error

        self.assertEqual('', network.Connection.send(self.mock, 'data'))
        self.mock.stop.assert_called_once_with(any_unicode)

    def test_timeout_callback(self):
        self.mock.timeout = 10

        self.assertFalse(network.Connection.timeout_callback(self.mock))
        self.mock.stop.assert_called_once_with(any_unicode)
