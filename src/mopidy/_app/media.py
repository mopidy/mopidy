from __future__ import annotations

import sys
import urllib.parse
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter, validators
from rich.console import Console
from rich.text import Text

from mopidy._app.model_tree import ModelTree
from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import (
    MediaReader,
    MediaReadError,
)
from mopidy.types import DurationMs, Uri

app = App(
    name="media",
    help="Display what Mopidy reads from files and URIs.",
)

Targets = Annotated[
    str,
    Parameter(help="Files or URIs to read."),
]
Timeout = Annotated[
    int,
    Parameter(
        name="--timeout",
        help="Timeout in milliseconds.",
        validator=validators.Number(gt=0),
    ),
]


@app.command(name="info")
def info(*targets: Targets, timeout: Timeout = 5000) -> None:
    """Display the media info of files or URIs."""
    console = Console()
    exit_code = 0
    config = Config.get_global()
    with MediaReader.create(config=config, timeout=DurationMs(timeout)) as media_reader:
        for uri in map(to_uri, targets):
            tree = ModelTree(Text(uri, overflow="fold"))
            try:
                media_info = media_reader.read_media_info(uri)
            except MediaReadError as exc:
                tree.add_leaf(
                    "error", str(exc), width=len("error"), wrap=True, style="red"
                )
                exit_code = 1
            else:
                tree.add_model(media_info)
            console.print(tree)
    sys.exit(exit_code)


@app.command(name="playlist-entries")
def playlist_entries(*targets: Targets, timeout: Timeout = 5000) -> None:
    """Display the entries of playlist documents."""
    console = Console()
    exit_code = 0
    config = Config.get_global()
    with MediaReader.create(config=config, timeout=DurationMs(timeout)) as media_reader:
        for uri in map(to_uri, targets):
            tree = ModelTree(Text(uri, overflow="fold"))
            try:
                playlist_entries = media_reader.read_playlist_entries(uri)
            except MediaReadError as exc:
                tree.add_leaf(
                    "error", str(exc), width=len("error"), wrap=True, style="red"
                )
                exit_code = 1
            else:
                if not playlist_entries:
                    tree.add_text("no playlist entries")
                for i, playlist_entry in enumerate(playlist_entries, start=1):
                    tree.add_value(str(i), playlist_entry, width=0, wrap=False)
            console.print(tree)
    sys.exit(exit_code)


@app.command(name="playback-target")
def playback_target(*targets: Targets, timeout: Timeout = 5000) -> None:
    """Display the URI to play for files or URIs.

    The timeout is the deadline for all reads for one file or URI.
    """
    console = Console()
    exit_code = 0
    config = Config.get_global()
    with MediaReader.create(config=config, timeout=DurationMs(timeout)) as media_reader:
        for uri in map(to_uri, targets):
            tree = ModelTree(Text(uri, overflow="fold"))
            playback_target = media_reader.find_playback_target(uri)
            if playback_target is None:
                tree.add_text(Text("no playback target found", style="red"))
                exit_code = 1
            else:
                tree.add_model(playback_target)
            console.print(tree)
    sys.exit(exit_code)


def to_uri(target: str) -> Uri:
    """Convert a command argument to a URI.

    An existing path becomes a `file` URI. Else, an argument with a URI scheme
    is a URI. Else, the argument is a path.
    """
    path = Path(target)
    if path.exists() or not urllib.parse.urlsplit(target).scheme:
        return path_to_uri(path.resolve())
    return Uri(target)
