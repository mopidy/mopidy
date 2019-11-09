import socket
import unittest
from unittest.mock import Mock, patch, sentinel

from mopidy.internal import network


class FormatHostnameTest(unittest.TestCase):
    @patch("mopidy.internal.network.has_ipv6", True)
    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        network.has_ipv6 = True
        assert network.format_hostname("0.0.0.0") == "::ffff:0.0.0.0"
        assert network.format_hostname("1.0.0.1") == "::ffff:1.0.0.1"

    @patch("mopidy.internal.network.has_ipv6", False)
    def test_format_hostname_does_nothing_when_only_ipv4_available(self):
        network.has_ipv6 = False
        assert network.format_hostname("0.0.0.0") == "0.0.0.0"


class FormatAddressTest(unittest.TestCase):
    def test_format_address_ipv4(self):
        address = (sentinel.host, sentinel.port)
        assert (
            network.format_address(address)
            == f"[{sentinel.host}]:{sentinel.port}"
        )

    def test_format_address_ipv6(self):
        address = (sentinel.host, sentinel.port, sentinel.flow, sentinel.scope)
        assert (
            network.format_address(address)
            == f"[{sentinel.host}]:{sentinel.port}"
        )

    def test_format_address_unix(self):
        address = (sentinel.path, None)
        assert network.format_address(address) == f"[{sentinel.path}]"


class GetSocketAddress(unittest.TestCase):
    def test_get_socket_address(self):
        host = str(sentinel.host)
        port = sentinel.port
        assert network.get_socket_address(host, port) == (host, port)

    def test_get_socket_address_unix(self):
        host = str(sentinel.host)
        port = sentinel.port
        assert network.get_socket_address(("unix:" + host), port) == (
            host,
            None,
        )


class TryIPv6SocketTest(unittest.TestCase):
    @patch("socket.has_ipv6", False)
    def test_system_that_claims_no_ipv6_support(self):
        assert not network.try_ipv6_socket()

    @patch("socket.has_ipv6", True)
    @patch("socket.socket")
    def test_system_with_broken_ipv6(self, socket_mock):
        socket_mock.side_effect = IOError()
        assert not network.try_ipv6_socket()

    @patch("socket.has_ipv6", True)
    @patch("socket.socket")
    def test_with_working_ipv6(self, socket_mock):
        socket_mock.return_value = Mock()
        assert network.try_ipv6_socket()


class CreateSocketTest(unittest.TestCase):
    @patch("mopidy.internal.network.has_ipv6", False)
    @patch("socket.socket")
    def test_ipv4_socket(self, socket_mock):
        network.create_tcp_socket()
        assert socket_mock.call_args[0] == (socket.AF_INET, socket.SOCK_STREAM)

    @patch("mopidy.internal.network.has_ipv6", True)
    @patch("socket.socket")
    def test_ipv6_socket(self, socket_mock):
        network.create_tcp_socket()
        assert socket_mock.call_args[0] == (socket.AF_INET6, socket.SOCK_STREAM)

    @unittest.SkipTest
    def test_ipv6_only_is_set(self):
        pass
