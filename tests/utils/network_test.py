import mock
import socket
import unittest

from mopidy.utils import network

from tests import SkipTest

class FormatHostnameTest(unittest.TestCase):
    @mock.patch('mopidy.utils.network.has_ipv6', True)
    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        network.has_ipv6 = True
        self.assertEqual(network.format_hostname('0.0.0.0'), '::ffff:0.0.0.0')
        self.assertEqual(network.format_hostname('1.0.0.1'), '::ffff:1.0.0.1')

    @mock.patch('mopidy.utils.network.has_ipv6', False)
    def test_format_hostname_does_nothing_when_only_ipv4_available(self):
        network.has_ipv6 = False
        self.assertEquals(network.format_hostname('0.0.0.0'), '0.0.0.0')


class TryIPv6SocketTest(unittest.TestCase):
    @mock.patch('socket.has_ipv6', False)
    def test_system_that_claims_no_ipv6_support(self):
        self.assertFalse(network._try_ipv6_socket())

    @mock.patch('socket.has_ipv6', True)
    @mock.patch('socket.socket')
    def test_system_with_broken_ipv6(self, socket_mock):
        socket_mock.side_effect = IOError()
        self.assertFalse(network._try_ipv6_socket())

    @mock.patch('socket.has_ipv6', True)
    @mock.patch('socket.socket')
    def test_with_working_ipv6(self, socket_mock):
        socket_mock.return_value = mock.Mock()
        self.assertTrue(network._try_ipv6_socket())


class CreateSocketTest(unittest.TestCase):
    @mock.patch('mopidy.utils.network.has_ipv6', False)
    @mock.patch('socket.socket')
    def test_ipv4_socket(self, socket_mock):
        network.create_socket()
        self.assertEqual(socket_mock.call_args[0],
            (socket.AF_INET, socket.SOCK_STREAM))

    @mock.patch('mopidy.utils.network.has_ipv6', True)
    @mock.patch('socket.socket')
    def test_ipv6_socket(self, socket_mock):
        network.create_socket()
        self.assertEqual(socket_mock.call_args[0],
            (socket.AF_INET6, socket.SOCK_STREAM))

    @SkipTest
    def test_ipv6_only_is_set(self):
        pass
