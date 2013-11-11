from __future__ import unicode_literals

import logging
import re
import socket
import string

logger = logging.getLogger('mopidy.utils.zerconf')

try:
    import dbus
except ImportError:
    dbus = None

_AVAHI_IF_UNSPEC = -1
_AVAHI_PROTO_UNSPEC = -1
_AVAHI_PUBLISHFLAGS_NONE = 0


def _filter_loopback_and_meta_addresses(host):
    # TODO: see if we can find a cleaner way of handling this.
    if re.search(r'(?<![.\d])(127|0)[.]', host):
        return ''
    return host


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
        self.host = _filter_loopback_and_meta_addresses(host or '')

        template = string.Template(name)
        self.name = template.safe_substitute(
            hostname=self.host or socket.getfqdn(), port=self.port)

    def publish(self):
        if not dbus:
            logger.debug('Zeroconf publish failed: dbus not installed.')
            return False

        try:
            bus = dbus.SystemBus()
        except dbus.exceptions.DBusException as e:
            logger.debug('Zeroconf publish failed: %s', e)
            return False

        if not bus.name_has_owner('org.freedesktop.Avahi'):
            logger.debug('Zeroconf publish failed: Avahi service not running.')
            return False

        server = dbus.Interface(bus.get_object('org.freedesktop.Avahi', '/'),
                                'org.freedesktop.Avahi.Server')

        self.group = dbus.Interface(
            bus.get_object('org.freedesktop.Avahi', server.EntryGroupNew()),
            'org.freedesktop.Avahi.EntryGroup')

        text = [_convert_text_to_dbus_bytes(t) for t in self.text]
        self.group.AddService(_AVAHI_IF_UNSPEC, _AVAHI_PROTO_UNSPEC,
                              dbus.UInt32(_AVAHI_PUBLISHFLAGS_NONE),
                              self.name, self.stype, self.domain, self.host,
                              dbus.UInt16(self.port), text)

        self.group.Commit()
        return True

    def unpublish(self):
        if self.group:
            self.group.Reset()
            self.group = None
