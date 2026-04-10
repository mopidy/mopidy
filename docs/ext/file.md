# mopidy-file

mopidy-file is an extension for playing music from your local music archive.
It is bundled with Mopidy and enabled by default.
It allows you to browse through your local file system.
Only files that are considered playable will be shown.
For large music collections and search functionality consider [mopidy-local](https://mopidy.com/ext/local/) instead.

This backend handles URIs starting with `file:`.

This backend does not currently provide images.

## Configuration

See [Configuration](../usage/config.md) for general help on configuring Mopidy.

```ini title="mopidy.conf"
[file]
enabled = true
media_dirs =
    $XDG_MUSIC_DIR|Music
    ~/|Home
show_dotfiles = false
excluded_file_extensions =
  .directory
  .html
  .jpeg
  .jpg
  .log
  .nfo
  .pdf
  .png
  .txt
  .zip
follow_symlinks = false
metadata_timeout = 1000
```

### file/enabled

If the file extension should be enabled or not.

### file/media_dirs

A list of directories to be browsable.
Optionally the path can be followed by `|` and a name that will be shown
for that path.

### file/show_dotfiles

Whether to show hidden files and directories that start with a dot.
Default is false.

### file/excluded_file_extensions

File extensions to exclude when scanning the media directory. Values
should be separated by either comma or newline.

### file/follow_symlinks

Whether to follow symbolic links found in [`file/media_dirs`](#filemedia_dirs).
Directories and files that are outside the configured directories will not
be shown. Default is false.

### file/metadata_timeout

Number of milliseconds before giving up scanning a file and moving on to
the next file. Reducing the value might speed up the directory listing,
but can lead to some tracks not being shown.
