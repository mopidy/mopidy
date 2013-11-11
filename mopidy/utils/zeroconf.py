import dbus

__all__ = ["Zeroconf"]

avahi_IF_UNSPEC = -1
avahi_PROTO_UNSPEC = -1
avahi_PublishFlags_None = 0


class Zeroconf:
    """A simple class to publish a network service with zeroconf using
    avahi.

    """

    def __init__(self, name, port, stype="_http._tcp",
                 domain="", host="", text=[]):
        self.name = name
        self.stype = stype
        self.domain = domain
        self.port = port
        self.text = text
        # Let avahi choose how to advertise services
        # listening on lo and meta addresses
        import re
        lo = re.search('(?<![.\d])(127|0)[.]', host)
        self.host = "" if lo else host

    def publish(self):
        bus = dbus.SystemBus()
        server = dbus.Interface(
            bus.get_object(
                "org.freedesktop.Avahi",
                "/"),
            "org.freedesktop.Avahi.Server")

        g = dbus.Interface(
            bus.get_object("org.freedesktop.Avahi",
                           server.EntryGroupNew()),
            "org.freedesktop.Avahi.EntryGroup")

        if self.text:
            self.text = [[dbus.Byte(ord(c)) for c in s] for s in self.text]

        g.AddService(avahi_IF_UNSPEC, avahi_PROTO_UNSPEC,
                     dbus.UInt32(avahi_PublishFlags_None),
                     self.name, self.stype, self.domain, self.host,
                     dbus.UInt16(self.port), self.text)

        g.Commit()
        self.group = g

    def unpublish(self):
        self.group.Reset()
