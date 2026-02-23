# mopidy command

## Synopsis

```text
mopidy
    [-h] [--version] [-q] [-v] [--config CONFIG_FILES] [-o CONFIG_OVERRIDES]
    [COMMAND] ...
```

## Description

Mopidy is a music server which can play music both from multiple sources, like
your local hard drive, radio streams, and from Spotify and SoundCloud. Searches
combines results from all music sources, and you can mix tracks from all
sources in your play queue. Your playlists from Spotify or SoundCloud are also
available for use.

The `mopidy` command is used to start the server.

## Options

**`--help`, `-h`**

Show help message and exit.

**`--version`**

Show Mopidy's version number and exit.

**`--quiet`, `-q`**

Show less output: warning level and higher.

**`--verbose`, `-v`**

Show more output. Repeat up to four times for even more.

**`--config <file|directory>`**

Specify config files and directories to use. To use multiple config files
or directories, separate them with a colon. The later files override the
earlier ones if there's a conflict. When specifying a directory, all files
ending in .conf in the directory are used.

**`--option <option>`, `-o <option>`**

Specify additional config values in the `section/key=value` format. Can
be provided multiple times.

## Built in commands

**`config`**

Show the current effective config. All configuration sources are merged
together to show the effective document. Secret values like passwords are
masked out. Config for disabled extensions are not included.

**`deps`**

Show dependencies, their versions and installation location.

## Extension commands

Additionally, extensions can provide extra commands. Run `mopidy --help`
for a list of what is available on your system and command-specific help.
Commands for disabled extensions will be listed, but can not be run.

## Files

`/etc/mopidy/mopidy.conf`
: System wide Mopidy configuration file.

`~/.config/mopidy/mopidy.conf`
: Your personal Mopidy configuration file. Overrides any configs from the
system wide configuration file.

## Examples

To start the music server, run:

```console
$ mopidy
```

To start the server with an additional config file, that can override configs
set in the default config files, run:

```console
$ mopidy --config ./my-config.conf
```

To start the server and change a config value directly on the command line,
run:

```console
$ mopidy --option mpd/enabled=false
```

The `--option` flag may be repeated multiple times to change multiple configs:

```console
$ mopidy -o mpd/enabled=false -o spotify/bitrate=320
```

The `mopidy config` output shows the effect of the `--option` flags:

```console
$ mopidy -o mpd/enabled=false -o spotify/bitrate=320 config
```

## Reporting bugs

Report bugs to Mopidy's issue tracker at
<https://github.com/mopidy/mopidy/issues>
