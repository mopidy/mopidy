# Clients

Once Mopidy is up and running, you need a client to control it.

Note that clients only *control* Mopidy. The audio itself is not
streamed to the clients, but it is played on the computer running
Mopidy. This is by design, as Mopidy was originally modelled after MPD.
If you want to stream audio from Mopidy to another device, the primary
options are [Icecast](../guides/icecast.md) and
[Snapcast](https://github.com/badaix/snapcast).

The most popular ways to control Mopidy are with web clients and with
MPD clients.

In addition, alternative frontends like [mopidy-mpris][mopidy-mpris] and
[mopidy-raspberry-gpio][mopidy-raspberry-gpio] provides additional ways to
control Mopidy. Alternative frontends that use a server-client architecture
usually list relevant clients in the extension's documentation.

## Web clients

There are many clients available that use
[mopidy-http](../ext/http.md) to control Mopidy.

### Web extensions

Mopidy extensions can make additional web APIs available through
Mopidy's builtin web server by implementing the
[HTTP server API](../reference/http-server.md). Web clients can use the
[HTTP API](../reference/http.md) to control Mopidy from JavaScript.

See the [Mopidy extension registry](https://mopidy.com/ext/) to find a
number of web clients can be easily installed as Mopidy extensions.

### Non-extension web clients

There are a few Mopidy web clients that are not installable as Mopidy
extensions:

- [Apollo Player](https://github.com/samcreate/Apollo-Player)
- [Mopster](https://github.com/cowbell/mopster)

### Web-based MPD clients

There are several web based MPD clients, which don't use
[mopidy-http](../ext/http.md) at all, but connect to Mopidy through the
[mopidy-mpd][mopidy-mpd]
frontend. For a list of those, see the "Web clients" section of the [MPD wiki's
clients list](https://mpd.fandom.com/wiki/Clients).

### Standalone applications

Lastly, there are Mopidy clients implemented as standalone applications:

- [Argos](https://github.com/orontee/argos)
- [Mopicon](https://github.com/nerk/mopicon)

## MPD clients

MPD is the protocol used by the original MPD server project since 2003.
The [mopidy-mpd][mopidy-mpd] extension provides a
server that implements the same protocol, and is compatible with most
MPD clients.

There are dozens of MPD clients available. Please refer to the
[mopidy-mpd][mopidy-mpd] extension's documentation for an overview.

## MPRIS clients

MPRIS is a specification that describes a standard D-Bus interface for
making media players available to other applications on the same system.

See the [mopidy-mpris][mopidy-mpris] documentation for
a survey of some MPRIS clients.

[mopidy-mpd]: https://mopidy.com/ext/mpd/
[mopidy-mpris]: https://mopidy.com/ext/mpris/
[mopidy-raspberry-gpio]: https://mopidy.com/ext/raspberry-gpio/
