from __future__ import annotations

import sys
import typing
import urllib.parse
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated

import pydantic
from cyclopts import App, Parameter, validators
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from mopidy._lib.paths import path_to_uri
from mopidy.config import Config
from mopidy.media import (
    EmbeddedImage,
    MediaReadError,
    Reader,
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
def info_command(*targets: Targets, timeout: Timeout = 5000) -> None:
    """Display the media info of files or URIs."""
    _run(info, targets, timeout)


@app.command(name="playlist-entries")
def playlist_entries_command(*targets: Targets, timeout: Timeout = 5000) -> None:
    """Display the entries of playlist documents."""
    _run(playlist_entries, targets, timeout)


@app.command(name="playback-target")
def playback_target_command(*targets: Targets, timeout: Timeout = 5000) -> None:
    """Display the URI to play for files or URIs.

    The timeout is the deadline for all reads for one file or URI.
    """
    _run(playback_target, targets, timeout)


def _run(
    func: Callable[[Reader, Sequence[str], Console], int],
    targets: Sequence[str],
    timeout: int,
) -> None:
    config = Config.get_global()
    with Reader.create(config=config, timeout=DurationMs(timeout)) as reader:
        exit_code = func(reader, targets, Console())
    sys.exit(exit_code)


def info(reader: Reader, targets: Sequence[str], console: Console) -> int:
    exit_code = 0
    for uri in map(to_uri, targets):
        tree = _root(uri)
        try:
            media_info = reader.read_media_info(uri)
        except MediaReadError as exc:
            _add_error(tree, str(exc))
            exit_code = 1
        else:
            _add_model(tree, media_info)
        console.print(tree)
    return exit_code


def playlist_entries(reader: Reader, targets: Sequence[str], console: Console) -> int:
    exit_code = 0
    for uri in map(to_uri, targets):
        tree = _root(uri)
        try:
            entries = reader.read_playlist_entries(uri)
        except MediaReadError as exc:
            _add_error(tree, str(exc))
            exit_code = 1
        else:
            if not entries:
                tree.add("no playlist entries")
            for i, entry in enumerate(entries, start=1):
                _add_model(tree.add(f"entry {i}"), entry)
        console.print(tree)
    return exit_code


def playback_target(reader: Reader, targets: Sequence[str], console: Console) -> int:
    exit_code = 0
    for uri in map(to_uri, targets):
        tree = _root(uri)
        target = reader.find_playback_target(uri)
        if target is None:
            tree.add(Text("no playback target found", style="red"))
            exit_code = 1
        else:
            width = len("entry")
            tree.add(_leaf("uri", target.uri, width=width, wrap=True))
            if target.info is None:
                unverified = Text("unverified", style="yellow")
                tree.add(_leaf("info", unverified, width=width))
            else:
                _add_model(tree.add("info"), target.info)
            if target.entry is not None:
                _add_model(tree.add("entry"), target.entry)
        console.print(tree)
    return exit_code


def to_uri(target: str) -> Uri:
    """Convert a command argument to a URI.

    An existing path becomes a `file` URI. Else, an argument with a URI scheme
    is a URI. Else, the argument is a path.
    """
    path = Path(target)
    if path.exists() or not urllib.parse.urlsplit(target).scheme:
        return path_to_uri(path.resolve())
    return Uri(target)


def _root(uri: Uri) -> Tree:
    return Tree(_text(uri, wrap=True))


def _add_error(tree: Tree, message: str) -> None:
    tree.add(_leaf("error", message, width=len("error"), wrap=True), style="red")


def _add_model(tree: Tree, model: pydantic.BaseModel) -> None:
    fields = [
        (name, value, _is_uri(field.annotation))
        for name, field in type(model).model_fields.items()
        if name != "model"  # The type name of Mopidy models
        and (value := getattr(model, name)) is not None
        and value not in ((), frozenset())
    ]
    width = max(
        (len(name) for name, value, _ in fields if not _is_branch(value)),
        default=0,
    )
    for name, value, wrap in fields:
        if _is_branch(value):
            _add_branch(tree.add(name), value, wrap=wrap)
        else:
            value = _format_value(name, value)
            tree.add(_leaf(name, value, width=width, wrap=wrap))


def _add_branch(tree: Tree, value: object, *, wrap: bool) -> None:
    if isinstance(value, pydantic.BaseModel):
        _add_model(tree, value)
        return
    assert isinstance(value, tuple | frozenset)
    items = sorted(value, key=repr) if isinstance(value, frozenset) else list(value)
    for i, item in enumerate(items, start=1):
        if isinstance(item, EmbeddedImage):
            tree.add(_text(f"{len(item.data)} bytes"))
        elif isinstance(item, pydantic.BaseModel):
            _add_model(tree.add(str(i)), item)
        else:
            tree.add(_text(str(item), wrap=wrap))


def _is_uri(annotation: object) -> bool:
    # Matches Uri, Uri | None and tuple[Uri, ...]
    return annotation is Uri or Uri in typing.get_args(annotation)


def _is_branch(value: object) -> bool:
    return isinstance(value, pydantic.BaseModel | tuple | frozenset)


def _format_value(name: str, value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if name == "length" and isinstance(value, int):
        return f"{value} ({_format_length(value)})"
    return str(value)


def _format_length(length: int) -> str:
    minutes, ms = divmod(length, 60_000)
    seconds, ms = divmod(ms, 1000)
    return f"{minutes}:{seconds:02d}.{ms:03d}"


def _leaf(
    name: str,
    value: str | Text,
    *,
    width: int,
    wrap: bool = False,
) -> Table:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(width=width, no_wrap=True)
    grid.add_column(no_wrap=not wrap, overflow="fold" if wrap else "ellipsis")
    grid.add_row(name, Text(value) if isinstance(value, str) else value)
    return grid


def _text(value: str, *, wrap: bool = False) -> Text:
    # URIs and error messages wrap. Other long values end with "…".
    if wrap:
        return Text(value, overflow="fold")
    return Text(value, no_wrap=True, overflow="ellipsis")
