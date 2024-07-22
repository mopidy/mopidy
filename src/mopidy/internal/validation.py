from __future__ import annotations

import urllib.parse
from collections.abc import Iterable, Mapping
from typing import Any, Literal, TypeVar, Union, get_args

from mopidy import exceptions
from mopidy.types import (
    DistinctField,
    PlaybackState,
    Query,
    QueryValue,
    SearchField,
    TracklistField,
)


def get_literals(literal_type: Any) -> set[str]:
    # Check if it's a union
    if hasattr(literal_type, "__origin__") and literal_type.__origin__ is Union:
        literals = set()
        for arg in get_args(literal_type):
            literals.update(get_literals(arg))
        return literals

    # Check if it's a literal
    if hasattr(literal_type, "__origin__") and literal_type.__origin__ is Literal:
        return set(get_args(literal_type))

    raise ValueError("Provided type is neither a Union nor a Literal type.")


T = TypeVar("T")

PLAYBACK_STATES: set[str] = {ps.value for ps in PlaybackState}

FIELD_TYPES: dict[str, type] = {
    "album": str,
    "albumartist": str,
    "any": int | str,
    "artist": str,
    "comment": str,
    "composer": str,
    "date": str,
    "disc_no": int,
    "genre": str,
    "musicbrainz_id": str,
    "musicbrainz_albumid": str,
    "musicbrainz_artistid": str,
    "musicbrainz_trackid": str,
    "name": str,
    "performer": str,
    "tlid": int,
    "track_name": str,
    "track_no": int,
    "uri": str,
}
DISTINCT_FIELDS: dict[str, type] = {
    x: FIELD_TYPES[x] for x in get_literals(DistinctField)
}
SEARCH_FIELDS: dict[str, type] = {x: FIELD_TYPES[x] for x in get_literals(SearchField)}
TRACKLIST_FIELDS: dict[str, type] = {
    x: FIELD_TYPES[x] for x in get_literals(TracklistField) - {"tlid"}
}


# TODO: _check_iterable(check, msg, **kwargs) + [check(a) for a in arg]?
def _check_iterable(
    arg,
    msg,
    **kwargs: Any,
) -> None:
    """Ensure we have an iterable which is not a string or an iterator"""
    if isinstance(arg, str):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))
    if not isinstance(arg, Iterable):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))
    if iter(arg) is iter(arg):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))


def check_choice(
    arg: T,
    choices: Iterable[T],
    msg: str = "Expected one of {choices}, not {arg!r}",
) -> None:
    if arg not in choices:
        raise exceptions.ValidationError(msg.format(arg=arg, choices=tuple(choices)))


def check_boolean(
    arg: bool,
    msg: str = "Expected a boolean, not {arg!r}",
) -> None:
    check_instance(arg, bool, msg=msg)


def check_instance(
    arg: T,
    cls: type[T],
    msg: str = "Expected a {name} instance, not {arg!r}",
) -> None:
    if not isinstance(arg, cls):
        raise exceptions.ValidationError(msg.format(arg=arg, name=cls.__name__))


def check_instances(
    arg: Iterable[Any],
    cls: type,
    msg: str = "Expected a list of {name}, not {arg!r}",
) -> None:
    _check_iterable(arg, msg, name=cls.__name__)
    if not all(isinstance(instance, cls) for instance in arg):
        raise exceptions.ValidationError(msg.format(arg=arg, name=cls.__name__))


def check_integer(
    arg: int,
    min: int | None = None,
    max: int | None = None,
) -> None:
    if not isinstance(arg, int):
        raise exceptions.ValidationError(f"Expected an integer, not {arg!r}")
    if min is not None and arg < min:
        raise exceptions.ValidationError(
            f"Expected number larger or equal to {min}, not {arg!r}"
        )
    if max is not None and arg > max:
        raise exceptions.ValidationError(
            f"Expected number smaller or equal to {max}, not {arg!r}"
        )


def check_query(
    arg: Query[SearchField] | Query[TracklistField],
    fields: Iterable[str] | None = None,
) -> None:
    if fields is None:
        fields = SEARCH_FIELDS.keys()
    # TODO: normalize name  -> track_name
    # TODO: normalize value -> [value]
    # TODO: normalize blank -> [] or just remove field?

    if not isinstance(arg, Mapping):
        raise exceptions.ValidationError(f"Expected a query dictionary, not {arg!r}")

    for key, value in arg.items():
        check_choice(
            key,
            fields,
            msg="Expected query field to be one of {choices}, not {arg!r}",
        )
        msg = 'Expected "{key}" to be list of strings, not {arg!r}'
        _check_iterable(value, msg, key=key)
        [_check_query_value(key, v, msg) for v in value]


def _check_query_value(
    key: DistinctField | (SearchField | TracklistField),
    arg: QueryValue,
    msg: str,
) -> None:
    if not isinstance(arg, str) or not arg.strip():
        raise exceptions.ValidationError(msg.format(arg=arg, key=key))


def check_uri(
    arg: str,
    msg="Expected a valid URI, not {arg!r}",
) -> None:
    if not isinstance(arg, str):
        raise exceptions.ValidationError(msg.format(arg=arg))
    if urllib.parse.urlparse(arg).scheme == "":
        raise exceptions.ValidationError(msg.format(arg=arg))


def check_uris(
    arg: Iterable[str],
    msg="Expected a list of URIs, not {arg!r}",
) -> None:
    _check_iterable(arg, msg)
    [check_uri(a, msg) for a in arg]
