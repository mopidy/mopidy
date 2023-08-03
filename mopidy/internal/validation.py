import urllib.parse
from collections.abc import Iterable, Mapping
from typing import Any, Optional, TypeVar, Union

from mopidy import exceptions

T = TypeVar("T")

PLAYBACK_STATES = {"paused", "stopped", "playing"}

TRACK_FIELDS_WITH_TYPES: dict[str, Union[type[str], type[int]]] = {
    "uri": str,
    "track_name": str,
    "album": str,
    "artist": str,
    "albumartist": str,
    "composer": str,
    "performer": str,
    "track_no": int,
    "genre": str,
    "date": str,
    "comment": str,
    "disc_no": int,
    "musicbrainz_albumid": str,
    "musicbrainz_artistid": str,
    "musicbrainz_trackid": str,
}

SEARCH_FIELDS = set(TRACK_FIELDS_WITH_TYPES).union({"any"})

PLAYLIST_FIELDS = {"uri", "name"}  # TODO: add length and last_modified?

TRACKLIST_FIELDS = {  # TODO: add bitrate, length, disc_no, track_no, modified?
    "uri",
    "name",
    "genre",
    "date",
    "comment",
    "musicbrainz_id",
}

DISTINCT_FIELDS = dict(TRACK_FIELDS_WITH_TYPES)


# TODO: _check_iterable(check, msg, **kwargs) + [check(a) for a in arg]?
def _check_iterable(
    arg,
    msg,
    **kwargs: Any,
) -> None:
    """Ensure we have an iterable which is not a string or an iterator"""
    if isinstance(arg, str):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))
    elif not isinstance(arg, Iterable):
        raise exceptions.ValidationError(msg.format(arg=arg, **kwargs))
    elif iter(arg) is iter(arg):
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
    min: Optional[int] = None,
    max: Optional[int] = None,
) -> None:
    if not isinstance(arg, int):
        raise exceptions.ValidationError(f"Expected an integer, not {arg!r}")
    elif min is not None and arg < min:
        raise exceptions.ValidationError(
            f"Expected number larger or equal to {min}, not {arg!r}"
        )
    elif max is not None and arg > max:
        raise exceptions.ValidationError(
            f"Expected number smaller or equal to {max}, not {arg!r}"
        )


def check_query(
    arg: dict[str, Any],
    fields: Optional[set[str]] = None,
    list_values: bool = True,
) -> None:
    if fields is None:
        fields = SEARCH_FIELDS
    # TODO: normalize name  -> track_name
    # TODO: normalize value -> [value]
    # TODO: normalize blank -> [] or just remove field?
    # TODO: remove list_values?

    if not isinstance(arg, Mapping):
        raise exceptions.ValidationError(f"Expected a query dictionary, not {arg!r}")

    for key, value in arg.items():
        check_choice(
            key,
            fields,
            msg="Expected query field to be one of {choices}, not {arg!r}",
        )
        if list_values:
            msg = 'Expected "{key}" to be list of strings, not {arg!r}'
            _check_iterable(value, msg, key=key)
            [_check_query_value(key, v, msg) for v in value]
        else:
            _check_query_value(
                key, value, 'Expected "{key}" to be a string, not {arg!r}'
            )


def _check_query_value(
    key: str,
    arg: Any,
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
    elif urllib.parse.urlparse(arg).scheme == "":
        raise exceptions.ValidationError(msg.format(arg=arg))


def check_uris(
    arg: Iterable[str],
    msg="Expected a list of URIs, not {arg!r}",
) -> None:
    _check_iterable(arg, msg)
    [check_uri(a, msg) for a in arg]
