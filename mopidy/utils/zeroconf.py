from __future__ import unicode_literals

try:
    import dbus
except ImportError:
    dbus = None

import re

_AVAHI_IF_UNSPEC = -1
_AVAHI_PROTO_UNSPEC = -1
_AVAHI_PUBLISHFLAGS_NONE = 0


def _filter_loopback_and_meta_addresses(host):
    # TODO: see if we can find a cleaner way of handling this.
    if re.search(r'(?<![.\d])(127|0)[.]', host):
        return ''
    return host


def _convert_text_to_dbus_bytes(text):
    return [[dbus.Byte(ord(c)) for c in s] for s in text]


class Zeroconf:
    """Publish a network service with zeroconf using avahi."""

    def __init__(self, name, port, stype="_http._tcp",
                 domain="", host="", text=[]):
        self.name = name
        self.stype = stype
        self.domain = domain
        self.port = port
        self.text = text
        self.host = _filter_loopback_and_meta_addresses(host)
        self.group = None

    def publish(self):
        bus = dbus.SystemBus()
        server = dbus.Interface(bus.get_object("org.freedesktop.Avahi", "/"),
                                "org.freedesktop.Avahi.Server")

        self.group = dbus.Interface(
            bus.get_object("org.freedesktop.Avahi", server.EntryGroupNew()),
            "org.freedesktop.Avahi.EntryGroup")

        text = _convert_text_to_dbus_bytes(self.text)
        self.group.AddService(_AVAHI_IF_UNSPEC, _AVAHI_PROTO_UNSPEC,
                              dbus.UInt32(_AVAHI_PUBLISHFLAGS_NONE),
                              self.name, self.stype, self.domain, self.host,
                              dbus.UInt16(self.port), text)

        self.group.Commit()

    def unpublish(self):
        if self.group:
            self.group.Reset()
            self.group = None
