from __future__ import absolute_import, unicode_literals

import logging
import socket
import string

logger = logging.getLogger(__name__)

try:
    import dbus
except ImportError:
    dbus = None

_AVAHI_IF_UNSPEC = -1
_AVAHI_PROTO_UNSPEC = -1
_AVAHI_PUBLISHFLAGS_NONE = 0


def _is_loopback_address(host):
    return (
        host.startswith('127.') or
        host.startswith('::ffff:127.') or
        host == '::1')


def _convert_text_list_to_dbus_format(text_list):
    array = dbus.Array(signature='ay')
    for text in text_list:
        array.append([dbus.Byte(ord(c)) for c in text])
    return array


class Zeroconf(object):

    """Publish a network service with Zeroconf.

    Currently, this only works on Linux using Avahi via D-Bus.

    :param str name: human readable name of the service, e.g. 'MPD on neptune'
    :param int port: TCP port of the service, e.g. 6600
    :param str stype: service type, e.g. '_mpd._tcp'
    :param str domain: local network domain name, defaults to ''
    :param str host: interface to advertise the service on, defaults to all
        interfaces
    :param text: extra information depending on ``stype``, defaults to empty
        list
    :type text: list of str
    """

    def __init__(self, name, port, stype=None, domain=None, text=None):
        self.group = None
        self.stype = stype or '_http._tcp'
        self.domain = domain or ''
        self.port = port
        self.text = text or []

        template = string.Template(name)
        self.name = template.safe_substitute(
            hostname=socket.getfqdn(), port=self.port)
        self.host = '%s.local' % socket.getfqdn()

    def __str__(self):
        return 'Zeroconf service %s at [%s]:%d' % (
            self.stype, self.host, self.port)

    def publish(self):
        """Publish the service.

        Call when your service starts.
        """

        if _is_loopback_address(self.host):
            logger.debug(
                '%s: Publish on loopback interface is not supported.', self)
            return False

        if not dbus:
            logger.debug('%s: dbus not installed; publish failed.', self)
            return False

        try:
            bus = dbus.SystemBus()

            if not bus.name_has_owner('org.freedesktop.Avahi'):
                logger.debug(
                    '%s: Avahi service not running; publish failed.', self)
                return False

            server = dbus.Interface(
                bus.get_object('org.freedesktop.Avahi', '/'),
                'org.freedesktop.Avahi.Server')

            self.group = dbus.Interface(
                bus.get_object(
                    'org.freedesktop.Avahi', server.EntryGroupNew()),
                'org.freedesktop.Avahi.EntryGroup')

            self.group.AddService(
                _AVAHI_IF_UNSPEC, _AVAHI_PROTO_UNSPEC,
                dbus.UInt32(_AVAHI_PUBLISHFLAGS_NONE), self.name, self.stype,
                self.domain, self.host, dbus.UInt16(self.port),
                _convert_text_list_to_dbus_format(self.text))

            self.group.Commit()
            logger.debug('%s: Published', self)
            return True
        except dbus.exceptions.DBusException as e:
            logger.debug('%s: Publish failed: %s', self, e)
            return False

    def unpublish(self):
        """Unpublish the service.

        Call when your service shuts down.
        """

        if self.group:
            try:
                self.group.Reset()
                logger.debug('%s: Unpublished', self)
            except dbus.exceptions.DBusException as e:
                logger.debug('%s: Unpublish failed: %s', self, e)
            finally:
                self.group = None
