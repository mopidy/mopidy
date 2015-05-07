from __future__ import absolute_import, unicode_literals

import socket
import unittest

from mock import Mock, patch

from mopidy.internal import network


class FormatHostnameTest(unittest.TestCase):

    @patch('mopidy.internal.network.has_ipv6', True)
    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        network.has_ipv6 = True
        self.assertEqual(network.format_hostname('0.0.0.0'), '::ffff:0.0.0.0')
        self.assertEqual(network.format_hostname('1.0.0.1'), '::ffff:1.0.0.1')

    @patch('mopidy.internal.network.has_ipv6', False)
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

    @patch('mopidy.internal.network.has_ipv6', False)
    @patch('socket.socket')
    def test_ipv4_socket(self, socket_mock):
        network.create_socket()
        self.assertEqual(
            socket_mock.call_args[0], (socket.AF_INET, socket.SOCK_STREAM))

    @patch('mopidy.internal.network.has_ipv6', True)
    @patch('socket.socket')
    def test_ipv6_socket(self, socket_mock):
        network.create_socket()
        self.assertEqual(
            socket_mock.call_args[0], (socket.AF_INET6, socket.SOCK_STREAM))

    @unittest.SkipTest
    def test_ipv6_only_is_set(self):
        pass
