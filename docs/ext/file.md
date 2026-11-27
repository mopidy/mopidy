# mopidy-file

mopidy-file is an extension for playing music from your local music archive.
It is bundled with Mopidy and enabled by default.
It allows you to browse through your local file system.
Only files that are considered playable will be shown.
For large music collections and search functionality consider [mopidy-local](https://mopidy.com/ext/local/) instead.

This backend handles URIs starting with `file:`.

A playlist document, such as a PLS or M3U file, plays as the first entry in it
that plays.

This backend does not currently provide images.

## CUE sheets

An album that is stored as one audio file, with a CUE sheet that says where each
track starts, is shown as an album. The sheet is shown as a directory with the
tracks, the audio file it describes is hidden, and each track plays only its
part of the file. Looking up the sheet gives all the tracks, with the titles,
artists, genre and date of the sheet.

- The tracks have URIs like `file:///music/Album.cue#3`, where the number is the
  position of the track in the sheet.
- A sheet can name many audio files, and the sheets and files can be in the same
  directory in any number. The sheet is matched to its file by the name in the
  sheet. If there is no such file, the match ignores the case, and the file
  extension, as sheets often name the `.wav` that a `.flac` came from.
- A sheet that cannot be used, such as a sheet that names a file that is missing, is
  shown as a file, and its audio files are not hidden. The reason is logged.
- A track ends where the next track in the same file starts. The silence in
  front of a track (`INDEX 00`) is the end of the previous track.
- The text in a CUE sheet is not always Unicode. See
  [`file/cue_encodings`](#filecue_encodings).
- Each track opens the audio file again and seeks to its start, so playing from
  one track to the next in the same file is not guaranteed to be gapless.

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
cue_sheets = true
cue_encodings =
  utf-8
  cp1252
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

### file/cue_sheets

Whether to show a CUE sheet as an album, with the tracks of the sheet.
If it is off, the CUE sheet and the audio file are shown as files.
Default is true.

### file/cue_encodings

The encodings to try, in order, for the text of a CUE sheet that is not
Unicode. Values should be separated by either comma or newline. Use the names
in the [Python list of standard
encodings](https://docs.python.org/3/library/codecs.html#standard-encodings).

A CUE sheet that starts with a byte order mark, or that is valid UTF-8, is
always read as such. For the other sheets the first encoding that can read the
whole sheet is used. There is no way to know which of the old encodings a sheet
is in, and many of them can read any bytes. Put the encodings that you need in
the order that gives the right text, and the one that reads anything last.
For example, for sheets with Russian text use `cp1251`, for Japanese
`shift_jis`, for Simplified Chinese `gbk`, for Traditional Chinese `big5` and
for Korean `euc_kr`:

```ini
cue_encodings =
  utf-8
  shift_jis
  cp1251
  cp1252
```

Default is `utf-8` and `cp1252`.
