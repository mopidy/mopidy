# PulseAudio

When [running Mopidy as a service](../usage/service.md), it runs as the
`mopidy` system user rather than your own user. PulseAudio runs as your main
user, so Mopidy can't access it directly. Running PulseAudio as a system-wide
daemon is [discouraged by
upstream](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/WhatIsWrongWithSystemWide/).
Instead, you can configure PulseAudio and Mopidy so that Mopidy sends audio
over TCP to the PulseAudio server already running as your main user.

First, configure PulseAudio to accept sound over TCP from localhost by
uncommenting or adding the TCP module to
`/etc/pulse/default.pa` or `$XDG_CONFIG_HOME/pulse/default.pa` (typically
`~/.config/pulse/default.pa`):

```plain title="default.pa"
### Network access (may be configured with paprefs, so leave this commented
### here if you plan to use paprefs)
#load-module module-esound-protocol-tcp
load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1
#load-module module-zeroconf-publish
```

Next, configure Mopidy to use this PulseAudio server:

```ini title="mopidy.conf"
[audio]
output = pulsesink server=127.0.0.1
```

After this, restart both PulseAudio and Mopidy:

```console
$ pulseaudio --kill
$ start-pulseaudio-x11
$ sudo systemctl restart mopidy
```

If you are not running any X server, run `pulseaudio --start` instead of
`start-pulseaudio-x11`.

If you don't want to hard code the output in your Mopidy config, you can instead
of adding any config to Mopidy add this to `~mopidy/.pulse/client.conf`:

```text title="~mopidy/.pulse/client.conf"
default-server=127.0.0.1
```
