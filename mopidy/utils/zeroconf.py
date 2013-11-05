import dbus

__all__ = ["Zeroconf"]


class Zeroconf:
    """A simple class to publish a network service with zeroconf using
    avahi.

    """

    def __init__(self, name, port, stype="_http._tcp",
                 domain="", host="", text=""):
        self.name = name
        self.stype = stype
        self.domain = domain
        self.host = host
        self.port = port
        self.text = text

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

        g.AddService(-1, -1, dbus.UInt32(0),
                     self.name, self.stype, self.domain, self.host,
                     dbus.UInt16(self.port), self.text)

        g.Commit()
        self.group = g

    def unpublish(self):
        self.group.Reset()
