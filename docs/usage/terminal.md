# Running in a terminal

For most users, it is probably preferable to run Mopidy as a
[service](service.md) so that Mopidy is automatically started when your system
starts.

The primary use case for running Mopidy manually in a terminal is that you're
developing on Mopidy or a Mopidy extension yourself, and are interested in
seeing the log output all the time and to be able to quickly start and restart
Mopidy.

## Starting

To start Mopidy manually, open a terminal and run:

```console
$ mopidy -v
12:07:13 INFO     MainThread mopidy._app.cli
                  Starting Mopidy 4.0.0
         INFO     MainThread mopidy._app.config
                  Loading config from file:///home/jodal/.config/mopidy/mopidy.conf
         INFO     MainThread mopidy._app.extensions
                  Enabled extensions: alsamixer, api_explorer, beets, file, http, local, m3u,
                  mpd, mpris, nad, orfradio, scrobbler, softwaremixer, spotify, stream
         INFO     MainThread mopidy._app.extensions
                  Disabled extensions: pandora, soundcloud
```

For a complete reference to the Mopidy commands and their command line
options, see [Commands](../reference/command.md).

You can also get some help directly in the terminal by running:

```console
$ mopidy --help
Usage: mopidy COMMAND

╭─ Commands ───────────────────────────────────────────────────────────────────────────────────╮
│ config       Display currently active configuration.                                         │
│ deps         Display installed extensions and their dependencies.                            │
│ local        Local extension commands.                                                       │
│ spotify      Spotify extension commands.                                                     │
│ --help (-h)  Display this message and exit.                                                  │
│ --version    Display application version.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Global parameters ──────────────────────────────────────────────────────────────────────────╮
│ --config      Config files to use. Repeat parameter or separate values with colon to use     │
│               multiple files. Later files have higher precedence. [default:                  │
│               /etc/mopidy/mopidy.conf, /home/jodal/.config/mopidy/mopidy.conf]               │
│ --option -o   Override config values. Repeat parameter to override multiple values. Format:  │
│               SECTION/KEY=VALUE.                                                             │
│ --quiet -q    Decrease amount of output to a minimum. [default: False]                       │
│ --verbose -v  Increase amount of output. Repeat up to four times for more. [default: 0]      │
╰──────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Stopping

To stop Mopidy, press ++ctrl+c++ in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the `TERM` signal to
the Mopidy process, e.g. by using `pkill` in another terminal:

```console
$ pkill mopidy
```

## Configuration

When running Mopidy for the first time, it'll create a configuration
file for you, usually at `~/.config/mopidy/mopidy.conf`.

The `~` in the file path automatically expands to your *home directory*.
If your username is `alice` and you are running Linux, the config file
will probably be at `/home/alice/.config/mopidy/mopidy.conf`.

As this might vary slightly from system to system, you can check the
first few lines of output from Mopidy to confirm the exact location:

```console hl_lines="7"
$ mopidy -v
20:34:36 INFO     MainThread mopidy._app.cli
                  Starting Mopidy 4.0.0
         INFO     MainThread mopidy._lib.paths
                  Creating file file:///home/jodal/.config/mopidy/mopidy.conf
         INFO     MainThread mopidy._app.cli
                  Initialized file:///home/jodal/.config/mopidy/mopidy.conf with default config
         INFO     MainThread mopidy._app.config
                  Loading config from file:///home/jodal/.config/mopidy/mopidy.conf
```

To print Mopidy's *effective* configuration, i.e. the combination of
defaults, your configuration file, and any command line options, you can
run:

```console
$ mopidy config
```

This will print your full effective config with passwords masked out so
that you safely can share the output with others for debugging.
