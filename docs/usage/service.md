# Running as a service

By running Mopidy as a system service, using e.g. systemd, it will
automatically be started when your system starts. This is the preferred
way to run Mopidy for most users.

The exact way Mopidy behaves when it runs as a service might vary
depending on your operating system or distribution. The following
applies to Debian, Ubuntu, Raspberry Pi OS, and Arch Linux. Hopefully,
other distributions packaging Mopidy will make sure this works the same
way on their distribution.

## Configuration

When running Mopidy as a system service, configuration is read from
`/etc/mopidy/mopidy.conf`, and not from `~/.config/mopidy/mopidy.conf`.

To print Mopidy's *effective* configuration, i.e. the combination of
defaults, your configuration file, and any command line options, you can
run:

```console
$ sudo mopidyctl config
```

This will print your full effective config with passwords masked out so
that you safely can share the output with others for debugging.

## Service user

The Mopidy system service runs as the `mopidy` user, which is
automatically created when you install the Mopidy package. The `mopidy`
user will need read access to any local music you want Mopidy to play.

/// note | Distribution packaging
If you're packaging Mopidy for a new distribution, make sure to
automatically create the `mopidy` user when the package is installed.
///

## Subcommands

To run Mopidy subcommands with the same user and config files as the
service uses, you should use `sudo mopidyctl <subcommand>`.

In other words, where someone running Mopidy manually in a terminal
would run:

```console
$ mopidy <subcommand>
```

You should instead run the following:

```console
$ sudo mopidyctl <subcommand>
```

/// note | Distribution packaging
If you're packaging Mopidy for a new distribution, you'll find the
`mopidyctl` command in the `extra/mopidyctl/` directory in the Mopidy Git
repository.
///

## Service management with systemd

On systems using systemd you can enable the Mopidy service by running:

```console
$ sudo systemctl enable mopidy
```

This will make Mopidy automatically start when the system starts.

Mopidy is started, stopped, and restarted just like any other systemd
service:

```console
$ sudo systemctl start mopidy
$ sudo systemctl stop mopidy
$ sudo systemctl restart mopidy
```

You can check if Mopidy is currently running as a service by running:

```console
$ sudo systemctl status mopidy
```

You can use `journalctl` to view Mopidy's log, including important
error messages:

```console
$ sudo journalctl -u mopidy
```

`journalctl` has many useful options, including `-f/--follow` and
`-e/--pager-end`, so please check out `journalctl --help` and
`man journalctl`.

## Service management on macOS

On macOS, you can use `launchctl` to start Mopidy automatically at login
as your own user.

/// tab | With Homebrew
If you installed Mopidy from Homebrew, simply run `brew info mopidy` and
follow the instructions in the "Caveats" section:

```console
$ brew info mopidy
...
==> Caveats
To have launchd start mopidy/mopidy/mopidy now and restart at login:
    brew services start mopidy/mopidy/mopidy
Or, if you don't want/need a background service, you can just run:
    mopidy
```

See `brew services --help` for how to start/restart/stop the service.
///

/// tab | Without Homebrew
If you happen to be on macOS, but didn't install Mopidy with Homebrew,
you can get the same effect by adding the file
`~/Library/LaunchAgents/mopidy.plist` with the following contents:

```xml title="~/Library/LaunchAgents/mopidy.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>mopidy</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/mopidy</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
```

You might need to adjust the path to the `mopidy` executable,
`/usr/local/bin/mopidy`, to match your system.

Then, to start Mopidy with `launchctl` right away:

```console
$ launchctl load ~/Library/LaunchAgents/mopidy.plist
```

///

## Audio daemons

If you use PulseAudio or PipeWire, the system service runs as its own user and
can't access your user-level audio daemon directly. See the dedicated guides for
how to configure each:

- [PulseAudio](../guides/pulseaudio.md)
- [PipeWire](../guides/pipewire.md)
