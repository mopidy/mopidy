from __future__ import annotations

import typing

import pydantic
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from mopidy.types import Uri


class ModelTree:
    """A Rich tree that shows the fields of models as key-value leaves."""

    def __init__(self, label: str | Text) -> None:
        self._tree = Tree(label)

    def __rich__(self) -> Tree:
        return self._tree

    def add_model(self, model: pydantic.BaseModel) -> None:
        """Add a node for each field of the model.

        Fields that are `None` are left out, except for related models. Empty
        tuples and sets are also left out.
        """
        fields = [
            (name, value, _is_uri_annotation(field.annotation))
            for name, field in type(model).model_fields.items()
            if name != "model"  # The type name of Mopidy models
            and (
                (value := getattr(model, name)) is not None
                or _is_model_annotation(field.annotation)
            )
            and value not in ((), frozenset())
        ]
        width = max(
            (len(name) for name, value, _ in fields if _is_leaf_value(value)),
            default=0,
        )
        for name, value, wrap in fields:
            self.add_value(name, value, width=width, wrap=wrap)

    def add_value(
        self,
        label: str,
        value: object,
        *,
        width: int,
        wrap: bool,
    ) -> None:
        """Add a node for a value.

        A model or a collection becomes a branch. Other values become a
        key-value leaf, with the key column `width` characters wide.
        """
        match value:
            case pydantic.BaseModel():
                self._add_branch(label).add_model(value)
            case tuple() | frozenset():
                branch = self._add_branch(label)
                items = (
                    sorted(value, key=repr) if isinstance(value, frozenset) else value
                )
                for i, item in enumerate(items, start=1):
                    branch.add_value(
                        str(i), item, width=len(str(len(items))), wrap=wrap
                    )
            case _:
                self.add_leaf(
                    label, _format_value(label, value), width=width, wrap=wrap
                )

    def add_leaf(
        self,
        key: str,
        value: str | Text,
        *,
        width: int,
        wrap: bool = False,
        style: str = "",
    ) -> None:
        """Add a key-value leaf.

        URIs and error messages wrap. Other long values end with "…".
        """
        # The value column gets the space that is left, so that a long value
        # does not make the key column narrower.
        grid = Table.grid(padding=(0, 2, 0, 0), expand=True)
        grid.add_column(width=width, no_wrap=True)
        grid.add_column(
            no_wrap=not wrap, overflow="fold" if wrap else "ellipsis", ratio=1
        )
        grid.add_row(key, Text(value) if isinstance(value, str) else value)
        self._tree.add(grid, style=style)

    def add_text(self, text: str | Text) -> None:
        """Add a leaf with only text."""
        self._tree.add(text)

    def _add_branch(self, label: str) -> ModelTree:
        branch = ModelTree(label)
        self._tree.children.append(branch._tree)
        return branch


def _is_uri_annotation(annotation: object) -> bool:
    # Matches Uri, Uri | None and tuple[Uri, ...]
    return annotation is Uri or Uri in typing.get_args(annotation)


def _is_model_annotation(annotation: object) -> bool:
    # Matches a model type, also in a union such as MediaInfo | None
    return any(
        isinstance(arg, type) and issubclass(arg, pydantic.BaseModel)
        for arg in (annotation, *typing.get_args(annotation))
    )


def _is_leaf_value(value: object) -> bool:
    return not isinstance(value, pydantic.BaseModel | tuple | frozenset)


def _format_value(name: str, value: object) -> str:
    if value is None:
        return "none"
    if isinstance(value, bytes):
        return f"{len(value)} bytes"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if name == "length" and isinstance(value, int):
        return f"{value} ({_format_length(value)})"
    return str(value)


def _format_length(length: int) -> str:
    minutes, ms = divmod(length, 60_000)
    seconds, ms = divmod(ms, 1000)
    return f"{minutes}:{seconds:02d}.{ms:03d}"
