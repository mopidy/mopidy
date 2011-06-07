import unittest

from mopidy.utils import network

class FormatHostnameTest(unittest.TestCase):
    def setUp(self):
        self.has_ipv6 = network.has_ipv6

    def tearDown(self):
        network.has_ipv6 = self.has_ipv6

    def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(self):
        network.has_ipv6 = True
        self.assertEqual(network.format_hostname('0.0.0.0'), '::ffff:0.0.0.0')
        self.assertEqual(network.format_hostname('1.0.0.1'), '::ffff:1.0.0.1')

    def test_format_hostname_does_nothing_when_only_ipv4_available(self):
        network.has_ipv6 = False
        self.assertEquals(network.format_hostname('0.0.0.0'), '0.0.0.0')
