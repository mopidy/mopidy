# Spotify on Debian

This guide describes how to set up Mopidy with Spotify support on a Debian-based
system with Debian 13 Trixie or equivalent, like Ubuntu 25.10 or Raspberry Pi OS
2025-12-04, or newer.

If you're using a Raspberry Pi, we recommend following the instructions in the
[Raspberry Pi guide](../guides/raspberrypi.md) before following the instructions
in this guide to install and configure Mopidy.

In this guide, we'll show how to install Mopidy and both the mopidy-mpd and
mopidy-spotify extensions from the APT repository.

For any other extensions, please follow our [general installation
instructions](../installation/index.md). The general instructions cover both
installing from the APT repository and installing using pip, but we recommend
using the APT repository when possible, as it makes it easier to keep Mopidy and
its extensions up-to-date with the rest of the system.

## Preparations

Before we begin, ensure that your system is fully up-to-date:

```console
$ sudo apt update
$ sudo apt upgrade -y
```

## Install Mopidy

Let's begin by installing Mopidy with the mopidy-mpd extension from Mopidy's own
APT repository:

```console
$ sudo wget -q -O /etc/apt/keyrings/mopidy-archive-keyring.gpg \
  https://apt.mopidy.com/mopidy-archive-keyring.gpg
$ sudo wget -q -O /etc/apt/sources.list.d/mopidy.sources \
  https://apt.mopidy.com/trixie.sources
$ sudo apt update
$ sudo apt install mopidy mopidy-mpd
```

You can now run `mopidy deps` to check that everything is installed correctly:

```console
$ mopidy deps
Executable: /usr/bin/mopidy
Platform: Linux-6.18.39+rpt-rpi-v8-aarch64-with-glibc2.41
Python: CPython 3.13.5 from /usr/lib/python3.13
mopidy: 4.0.3 from /usr/lib/python3/dist-packages
  cyclopts: 3.12.0 from /usr/lib/python3/dist-packages
    attrs: 25.3.0 from /usr/lib/python3/dist-packages
    docstring-parser: 0.16 from /usr/lib/python3/dist-packages
    importlib-metadata: not found
    rich: 13.9.4 from /usr/lib/python3/dist-packages
      markdown-it-py: 3.0.0 from /usr/lib/python3/dist-packages
        mdurl: 0.1.2 from /usr/lib/python3/dist-packages
      pygments: 2.18.0 from /usr/lib/python3/dist-packages
      typing-extensions: 4.13.2 from /usr/lib/python3/dist-packages
    rich-rst: 1.3.1 from /usr/lib/python3/dist-packages
      docutils: 0.21.2 from /usr/lib/python3/dist-packages
  httpx: 0.28.1 from /usr/lib/python3/dist-packages
    anyio: 4.8.0 from /usr/lib/python3/dist-packages
      exceptiongroup: not found
      idna: 3.10 from /usr/lib/python3/dist-packages
      sniffio: 1.3.1 from /usr/lib/python3/dist-packages
      typing_extensions: 4.13.2 from /usr/lib/python3/dist-packages
    certifi: 2025.1.31 from /usr/lib/python3/dist-packages
    httpcore: 1.0.7 from /usr/lib/python3/dist-packages
      h11: 0.14.0 from /usr/lib/python3/dist-packages
  platformdirs: 4.3.7 from /usr/lib/python3/dist-packages
  pydantic: 2.10.6 from /usr/lib/python3/dist-packages
    annotated-types: 0.7.0 from /usr/lib/python3/dist-packages
    pydantic-core: 2.27.2 from /usr/lib/python3/dist-packages
  pygobject: 3.50.0 from /usr/lib/python3/dist-packages
  pykka: 4.1.1 from /usr/lib/python3/dist-packages
  rich: 13.9.4 from /usr/lib/python3/dist-packages
  tornado: 6.4.2 from /usr/lib/python3/dist-packages
mopidy-mpd: 4.0.1 from /usr/lib/python3/dist-packages
  mopidy: 4.0.3 from /usr/lib/python3/dist-packages
  pygobject: 3.50.0 from /usr/lib/python3/dist-packages
  pykka: 4.1.1 from /usr/lib/python3/dist-packages
GStreamer: 1.26.2.0
  Available elements:
    uridecodebin: 1.26.2
    souphttpsrc: 1.26.2
    alsasink: 1.26.2
    osssink: 1.26.2
    oss4sink: 1.26.2
    pulsesink: 1.26.2
    id3demux: 1.26.2
    id3v2mux: 1.26.2
    lamemp3enc: 1.26.2
    mpegaudioparse: 1.26.2
    mpg123audiodec: 1.26.2
    vorbisdec: 1.26.2
    vorbisenc: 1.26.2
    vorbisparse: 1.26.2
    oggdemux: 1.26.2
    oggmux: 1.26.2
    oggparse: 1.26.2
    flacdec: 1.26.2
    flacparse: 1.26.2
    shout2send: 1.26.2
  Missing elements:
    flump3dec
    mad
```

## Enable and start the service

Now we're ready to enable the Mopidy service, so that it starts at boot, and
start the service:

```console
$ sudo systemctl enable --now mopidy
```

We can check that the service is running with:

```console hl_lines="4"
$ systemctl status mopidy
● mopidy.service - Mopidy music server
     Loaded: loaded (/usr/lib/systemd/system/mopidy.service; enabled; preset: enabled)
     Active: active (running) since Sun 2026-04-12 17:55:21 CEST; 4min 57s ago
 Invocation: ed14f137cee44a68ad008eb877d3395a
    Process: 3813 ExecStartPre=/bin/mkdir -p /var/cache/mopidy (code=exited, status=0/SUCCESS)
    Process: 3815 ExecStartPre=/bin/chown mopidy:audio /var/cache/mopidy (code=exited, status=0/SUCCESS)
   Main PID: 3817 (mopidy)
      Tasks: 11 (limit: 764)
        CPU: 3.387s
     CGroup: /system.slice/mopidy.service
             └─3817 /usr/bin/python3 /usr/bin/mopidy --config /usr/share/mopidy/conf.d:/etc/mopidy/mopidy.conf

Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy.commands Starting Mopidy mixer: SoftwareMixer
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy.commands Starting Mopidy audio
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy.commands Starting Mopidy backends: FileBackend, M3UBacken>
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [Audio-2 (_actor_loop)] mopidy.audio.actor Audio output set to "autoaudiosink"
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy.commands Starting Mopidy core
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy.commands Starting Mopidy frontends: HttpFrontend, MpdFron>
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [HttpFrontend-8 (_actor_loop)] mopidy.http.actor HTTP server running at [::ff>
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy_mpd.actor MPD server running at [::ffff:127.0.0.1]:6600
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy.commands Starting GLib mainloop
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [HttpServer] mopidy.internal.path Creating dir file:///var/lib/mopidy/http
```

To tail the logs in real time, you can run:

```console
$ journalctl -u mopidy -f
```

Hit ++ctrl+c++ to stop tailing the logs.

If we look closer at the logs, we can see that both the MPD and HTTP server have
started, but are only listening for connections on the loopback interface, which
means that we won't be able to connect to them from other devices on the
network.

```console
$ journalctl -u mopidy | grep "server running"
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [HttpFrontend-8 (_actor_loop)] mopidy.http.actor HTTP server running at [::ffff:127.0.0.1]:6680
Apr 12 17:55:25 hipup mopidy[3817]: INFO     [MainThread] mopidy_mpd.actor MPD server running at [::ffff:127.0.0.1]:6600
```

We need to change the configuration to allow that.

## Enable network access to the HTTP and MPD servers

To enable both the bundled [HTTP](../ext/http.md) server and the [MPD](https://mopidy.com/ext/mpd/)
server we installed with the `mopidy-mpd` package to listen on all network
interfaces, add the following lines to the `/etc/mopidy/mopidy.conf`
configuration file:

```ini title="/etc/mopidy/mopidy.conf"
[http]
hostname = ::

[mpd]
hostname = ::
```

You can edit the configuration file using e.g. `nano`:

```console
$ sudo nano /etc/mopidy/mopidy.conf
```

Press ++ctrl+o++ to save the file, and ++ctrl+x++ to exit the editor.

You can check that the changes are correctly read by Mopidy by asking Mopidy to
print its effective configuration, including all default values, with:

```console
$ sudo mopidyctl config
Running "/usr/bin/mopidy --config /usr/share/mopidy/conf.d:/etc/mopidy/mopidy.conf config" as user mopidy
[core]
cache_dir = /var/cache/mopidy
config_dir = /etc/mopidy
data_dir = /var/lib/mopidy
max_tracklist_length = 10000
restore_state = false
...
```

Now, we need to restart the Mopidy service to apply the changes:

```console
$ sudo systemctl restart mopidy
```

To confirm that the servers are listening on all interfaces we can look at the
logs again, confirming that `::ffff:127.0.0.1` has been replaced with `::`,
which means all IPv4 and IPv6 interfaces.

```console
$ journalctl -u mopidy | grep "server running"
Apr 12 18:14:34 hipup mopidy[3954]: INFO     [HttpFrontend-10 (_actor_loop)] mopidy.http.actor HTTP server running at [::]:6680
Apr 12 18:14:34 hipup mopidy[3954]: INFO     [MainThread] mopidy_mpd.actor MPD server running at [::]:6600
```

You should now be able to connect to the HTTP and MPD servers from other devices
on the network, using the Pi's IP address and the respective ports (6680 for
HTTP and 6600 for MPD). For example, you can open `http://<ip-address>:6680/` in
a web browser to access the HTTP server, or connect to the MPD server using a
terminal-based MPD client like `ncmpcpp`:

```console
$ sudo apt install ncmpcpp
$ ncmpcpp -h <ip-address>
```

## Install the Spotify extension

The [mopidy-spotify](https://mopidy.com/ext/spotify/) extension is in the same
APT repository as Mopidy itself:

```console
$ sudo apt install mopidy-spotify
```

/// note | The GStreamer Spotify plugin
The extension needs the `gst-plugin-spotify` GStreamer plugin for the playback.
The `mopidy-spotify` package depends on that plugin, so `apt` installs it for
you. Debian does not have the plugin, so we maintain
[gst-plugins-rs-build](https://github.com/mopidy/gst-plugins-rs-build) to build
it, and the APT repository has it for amd64, arm64, armhf and riscv64. On any
other architecture, you must build the plugin yourself, as described in the
[gst-plugins-rs-build
README](https://github.com/mopidy/gst-plugins-rs-build#readme).
///

You can now check that the plugin was installed correctly by running
`gst-inspect-1.0 spotify`:

```console
$ gst-inspect-1.0 spotify
Plugin Details:
  Name                     spotify
  Description              GStreamer Spotify Plugin
  Filename                 /usr/lib/aarch64-linux-gnu/gstreamer-1.0/libgstspotify.so
  Version                  0.16.0-alpha-b9abdbc
  License                  MPL
  Source module            gst-plugin-spotify
  Documentation            https://gstreamer.freedesktop.org/documentation/spotify/
  Source release date      2026-08-20
  Binary package           gst-plugin-spotify
  Origin URL               https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs

  spotifyaudiosrc: Spotify source
  spotifylyricssrc: Spotify lyrics source

  2 features:
  +-- 2 elements
```

Using `mopidy deps`, we can check that Mopidy has detected the mopidy-spotify
extension:

```console hl_lines="7-15"
$ mopidy deps
Executable: /usr/bin/mopidy
Platform: Linux-6.18.39+rpt-rpi-v8-aarch64-with-glibc2.41
Python: CPython 3.13.5 from /usr/lib/python3.13
mopidy: 4.0.3 from /usr/lib/python3/dist-packages
  ...
mopidy-mpd: 4.0.1 from /usr/lib/python3/dist-packages
  ...
mopidy-spotify: 5.0.1 from /usr/lib/python3/dist-packages
  mopidy: 4.0.3 from /usr/lib/python3/dist-packages
  pykka: 4.1.1 from /usr/lib/python3/dist-packages
  requests: 2.32.3 from /usr/lib/python3/dist-packages
    charset_normalizer: 3.4.2 from /usr/lib/python3/dist-packages
    urllib3: 2.3.0 from /usr/lib/python3/dist-packages
GStreamer: 1.26.2.0
  Available elements:
    ...
    spotifyaudiosrc: 0.16.0-alpha-b9abdbc
    ...
  Missing elements:
    ...
```

## Authenticate with Spotify

If we restart the Mopidy service now, we should see in the logs that the
extension is there, but it is disabled because we haven't authenticated with
Spotify yet:

```console
$ journalctl -u mopidy | grep spotify
Apr 12 18:07:53 hipup mopidy[3906]: INFO     [MainThread] mopidy.__main__ Disabled extensions: spotify
Apr 12 18:07:53 hipup mopidy[3906]: WARNING  [MainThread] mopidy.__main__ Found spotify configuration errors. The extension has been automatically disabled:
Apr 12 18:07:53 hipup mopidy[3906]: WARNING  [MainThread] mopidy.__main__   spotify/client_id must be set.
Apr 12 18:07:53 hipup mopidy[3906]: WARNING  [MainThread] mopidy.__main__   spotify/client_secret must be set.
```

To authenticate the Mopidy extension with your Spotify account, go to
<https://mopidy.com/ext/spotify/> and follow the instructions to authenticate with
Spotify. Once you've logged in with Spotify and come back to the Mopidy website,
the page will show the exact configuration you need to add to your
`/etc/mopidy/mopidy.conf` file to enable Spotify playback. It should look
something like this:

```ini title="/etc/mopidy/mopidy.conf"
[spotify]
client_id = your-oauth-client-id
client_secret = your-oauth-client-secret
```

After editing `/etc/mopidy/mopidy.conf` again to add the Spotify config, restart
the Mopidy service again:

```console
$ sudo systemctl restart mopidy
```

## Play music from Spotify

If you have the very minimalistic `mpc` client installed, you can add a Spotify
track to the tracklist and start playback with:

```console
$ mpc -h <ip-address> add spotify:track:4mdsqeYQoEwCYl0gdnUCLC
$ mpc -h <ip-address> play
```

But it might be easier to use a more full-featured MPD client, like `ncmpcpp`,
which lets you browse the music library and playlists, and search for tracks and
artists, directly from the client interface.

Et voilà! You should now have a working Mopidy setup with Spotify support on
your Debian-based system. You can now explore the various MPD clients available,
or use the HTTP server to control playback from one of the many web clients.
Happy listening!
