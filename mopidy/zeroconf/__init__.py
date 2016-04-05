import logging
import sys

__all__ = ['Zeroconf']

logger = logging.getLogger(__name__)


def _is_loopback_address(host):
    return (
        host.startswith('127.') or
        host.startswith('::ffff:127.') or
        host == '::1')


class ZeroconfInterface(object):

    """Base class for Zeroconf implementations"""

    """Publish a network service with Zeroconf.

    :param str name: human readable name of the service, e.g. 'MPD on neptune'
    :param str stype: service type, e.g. '_mpd._tcp'
    :param int port: TCP port of the service, e.g. 6600
    :param str domain: local network domain name, defaults to ''
    :param str host: interface to advertise the service on, defaults to ''
    :param text: extra information depending on ``stype``, defaults to empty
        list
    :type text: list of str
    """
    def __init__(self, name, stype, port, domain='', host='', text=None):
        self.stype = stype
        self.port = port
        self.domain = domain
        self.host = host
        self.text = text or []

        self.group = None
        self.display_hostname = None
        self.name = None

    def __str__(self):
        return 'Zeroconf service "%s" (%s at [%s]:%d)' % (
            self.name, self.stype, self.host, self.port)

    def publish(self):
        raise NotImplementedError

    def unpublish(self):
        raise NotImplementedError


if sys.platform == 'darwin':
    logger.debug('Detected OSX, using pybonjour for Zeroconf.')
    from .pybonjour import Zeroconf
else:
    logger.debug('Assuming Linux, using Avahi via D-Bus for Zeroconf.')
    from .avahi import Zeroconf
