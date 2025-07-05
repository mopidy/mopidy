from mopidy.models import Album, Artist, Track


def base10_int_or_none(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value.strip(), 10)
    except ValueError:
        return None


def convert_tags_to_track(tags: dict) -> Track:
    return Track(
        name=tags.get("title"),
        artists=frozenset([Artist(name=tags["artist"])] if tags.get("artist") else ()),
        composers=frozenset(
            [Artist(name=tags["composer"])] if tags.get("composer") else ()
        ),
        album=Album(name=tags["album"]) if tags.get("album") else None,
        date=tags.get("date"),
        genre=tags.get("genre"),
        track_no=base10_int_or_none(tags.get("track")),
        disc_no=base10_int_or_none(tags.get("disc_number")),
        comment=tags.get("comment"),
    )
