import unittest
from unittest.mock import Mock, patch

from mopidy.internal import network


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
