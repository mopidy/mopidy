from __future__ import absolute_import, unicode_literals

import logging
import select
import string

from mopidy.zeroconf import ZeroconfInterface, _is_loopback_address

logger = logging.getLogger(__name__)

try:
    import pybonjour
except ImportError:
    pybonjour = None


class Zeroconf(ZeroconfInterface):

    """Publish a network service with Zeroconf using pybonjour

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
        ZeroconfInterface.__init__(self, name, stype, port, domain, host, text)

        if pybonjour:
            self.name = string.Template(name).safe_substitute(
                hostname=self.display_hostname, port=port)

    def register_callback(self, sdref, flags, errorcode, name, regtype,
                          domain):
        if errorcode == pybonjour.kDNSServiceErr_NoError:
            logger.debug(
                '%s: Registered service: name = %s, regtype = %s,'
                'domain = %s', self, name, regtype, domain)

    def publish(self):
        """Publish the service.

        Call when your service starts.
        """

        if _is_loopback_address(self.host):
            logger.debug(
                '%s: Publish on loopback interface is not supported.', self)
            return False

        if not pybonjour:
            logger.debug('%s: pybonjour not installed; publish failed.', self)
            return False

        self.sdref = pybonjour.DNSServiceRegister(
            name=self.name,
            regtype=self.stype, port=self.port,
            domain=self.domain,
            callBack=self.register_callback)

        processed = False
        while not processed:
            ready = select.select([self.sdref], [], [])
            if self.sdref in ready[0]:
                pybonjour.DNSServiceProcessResult(self.sdref)
                processed = True

        logger.debug('%s: Published', self)
        return True

    def unpublish(self):
        """Unpublish the service.

        Call when your service shuts down.
        """
        self.sdref.close()

        logger.debug('%s: Unpublished', self)
