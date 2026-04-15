# PipeWire

When [running Mopidy as a service](../usage/service.md), it runs as the
`mopidy` system user rather than your own user. PipeWire runs as your main
user, so Mopidy can't access it directly. As with [PulseAudio](pulseaudio.md),
you can configure PipeWire and Mopidy so that Mopidy sends audio over TCP to
the PipeWire server already running as your main user.

First make sure that `pipewire-pulse` is installed. It's PipeWire's PulseAudio
replacement.

Check whether a configuration file for `pipewire-pulse` is available (may depend
on the Linux distribution but `/etc/pipewire/pipewire-pulse.conf` is standard).
If not, copy from `/usr/share/pipewire/pipewire-pulse.conf`.

Then modify that file for `pipewire-pulse` to accept sound over TCP from
localhost (note the uncommented line with `"tcp:4713"`):

```text title="pipewire-pulse.conf" hl_lines="5"
pulse.properties = {
    # the addresses this server listens on
    server.address = [
        "unix:native"
        "tcp:4713"
    ]
```

Next, configure Mopidy to use this `pipewire-pulse` server:

```ini title="mopidy.conf"
[audio]
output = pulsesink server=127.0.0.1
```

After this, restart both PipeWire and Mopidy:

```console
$ systemctl --user restart pipewire pipewire-pulse
$ sudo systemctl restart mopidy
```
