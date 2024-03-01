from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from abc import abstractmethod
    from collections.abc import Iterable

    class Comparable(Protocol):
        @abstractmethod
        def __lt__(self: CT, other: CT, /) -> bool: ...

    T = TypeVar("T")
    CT = TypeVar("CT", bound=Comparable)


# TODO: add validate regexp?


def validate_required(value: Any, required: bool) -> None:
    """Validate that ``value`` is set if ``required``.

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize` on
    the raw string, _not_ the converted value.
    """
    if required and not value:
        raise ValueError("must be set.")


def validate_choice(value: T, choices: Iterable[T] | None) -> None:
    """Validate that ``value`` is one of the ``choices``.

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize`.
    """
    if choices is not None and value not in choices:
        names = ", ".join(repr(c) for c in choices)
        raise ValueError(f"must be one of {names}, not {value}.")


def validate_minimum(value: CT, minimum: CT | None) -> None:
    """Validate that ``value`` is at least ``minimum``.

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize`.
    """
    if minimum is not None and value < minimum:
        raise ValueError(f"{value!r} must be larger than {minimum!r}.")


def validate_maximum(value: CT, maximum: CT | None) -> None:
    """Validate that ``value`` is at most ``maximum``.

    Normally called in :meth:`~mopidy.config.types.ConfigValue.deserialize`.
    """
    if maximum is not None and value > maximum:
        raise ValueError(f"{value!r} must be smaller than {maximum!r}.")
