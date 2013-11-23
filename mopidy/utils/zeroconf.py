from __future__ import unicode_literals

import logging
import socket
import string

logger = logging.getLogger('mopidy.utils.zeroconf')

try:
    import dbus
except ImportError:
    dbus = None

_AVAHI_IF_UNSPEC = -1
_AVAHI_PROTO_UNSPEC = -1
_AVAHI_PUBLISHFLAGS_NONE = 0


def _is_loopback_address(host):
    return host.startswith('127.') or host == '::1'


def _convert_text_to_dbus_bytes(text):
    return [dbus.Byte(ord(c)) for c in text]


class Zeroconf(object):
    """Publish a network service with Zeroconf using Avahi."""

    def __init__(self, name, port, stype=None, domain=None,
                 host=None, text=None):
        self.group = None
        self.stype = stype or '_http._tcp'
        self.domain = domain or ''
        self.port = port
        self.text = text or []
        if host in ('::', '0.0.0.0'):
            self.host = ''
        else:
            self.host = host

        template = string.Template(name)
        self.name = template.safe_substitute(
            hostname=self.host or socket.getfqdn(), port=self.port)

    def publish(self):
        if _is_loopback_address(self.host):
            logger.info(
                'Zeroconf publish on loopback interface is not supported.')
            return False

        if not dbus:
            logger.debug('Zeroconf publish failed: dbus not installed.')
            return False

        try:
            bus = dbus.SystemBus()

            if not bus.name_has_owner('org.freedesktop.Avahi'):
                logger.debug(
                    'Zeroconf publish failed: Avahi service not running.')
                return False

            server = dbus.Interface(
                bus.get_object('org.freedesktop.Avahi', '/'),
                'org.freedesktop.Avahi.Server')

            self.group = dbus.Interface(
                bus.get_object(
                    'org.freedesktop.Avahi', server.EntryGroupNew()),
                'org.freedesktop.Avahi.EntryGroup')

            text = [_convert_text_to_dbus_bytes(t) for t in self.text]
            self.group.AddService(
                _AVAHI_IF_UNSPEC, _AVAHI_PROTO_UNSPEC,
                dbus.UInt32(_AVAHI_PUBLISHFLAGS_NONE), self.name, self.stype,
                self.domain, self.host, dbus.UInt16(self.port), text)

            self.group.Commit()
            return True
        except dbus.exceptions.DBusException as e:
            logger.debug('Zeroconf publish failed: %s', e)
            return False

    def unpublish(self):
        if self.group:
            try:
                self.group.Reset()
            except dbus.exceptions.DBusException as e:
                logger.debug('Zeroconf unpublish failed: %s', e)
            finally:
                self.group = None
