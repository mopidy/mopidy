from typing import Any

from mopidy import exceptions
from mopidy._lib.gi import Gst
from mopidy._lib.gst import convert_taglist, repr_tags
from mopidy.models import Album, Artist, Track
from mopidy.types import DurationMs, Uri

__all__ = [
    "convert_taglist",
    "convert_tags_to_track",
    "repr_tags",
]


# TODO: split based on "stream" and "track" based conversion? i.e. handle data
# from radios in it's own helper instead?
def convert_tags_to_track(
    tags: dict[str, Any],
    *,
    uri: Uri,
    length: DurationMs | None = None,
    last_modified: int | None = None,
) -> Track:
    """Convert our normalized tags to a track.

    Raises:
        exceptions.ScannerError: If the tags can't be coerced into a valid
            `Track`. Callers scanning multiple URIs should catch this per URI,
            so that a single file with broken tags doesn't fail the entire scan
            or lookup.
    """
    album_kwargs = dict[str, Any]()
    track_kwargs = dict[str, Any]()

    track_kwargs["composers"] = _artists(tags, Gst.TAG_COMPOSER)
    track_kwargs["performers"] = _artists(tags, Gst.TAG_PERFORMER)
    track_kwargs["artists"] = _artists(
        tags,
        Gst.TAG_ARTIST,
        "musicbrainz-artistid",
        "musicbrainz-sortname",
    )
    album_kwargs["artists"] = _artists(
        tags,
        Gst.TAG_ALBUM_ARTIST,
        "musicbrainz-albumartistid",
    )

    track_kwargs["genre"] = "; ".join(tags.get(Gst.TAG_GENRE, []))
    track_kwargs["name"] = "; ".join(tags.get(Gst.TAG_TITLE, []))
    if not track_kwargs["name"]:
        track_kwargs["name"] = "; ".join(tags.get(Gst.TAG_ORGANIZATION, []))

    track_kwargs["comment"] = "; ".join(tags.get("comment", []))
    if not track_kwargs["comment"]:
        track_kwargs["comment"] = "; ".join(tags.get(Gst.TAG_LOCATION, []))
    if not track_kwargs["comment"]:
        track_kwargs["comment"] = "; ".join(tags.get(Gst.TAG_COPYRIGHT, []))

    track_kwargs["track_no"] = tags.get(Gst.TAG_TRACK_NUMBER, [None])[0]
    track_kwargs["disc_no"] = tags.get(Gst.TAG_ALBUM_VOLUME_NUMBER, [None])[0]
    track_kwargs["bitrate"] = tags.get(Gst.TAG_BITRATE, [None])[0]
    track_kwargs["musicbrainz_id"] = tags.get("musicbrainz-trackid", [None])[0]

    album_kwargs["name"] = tags.get(Gst.TAG_ALBUM, [None])[0]
    album_kwargs["num_tracks"] = tags.get(Gst.TAG_TRACK_COUNT, [None])[0]
    album_kwargs["num_discs"] = tags.get(Gst.TAG_ALBUM_VOLUME_COUNT, [None])[0]
    album_kwargs["musicbrainz_id"] = tags.get("musicbrainz-albumid", [None])[0]

    album_kwargs["date"] = tags.get(Gst.TAG_DATE, [None])[0]
    if not album_kwargs["date"]:
        datetime = tags.get(Gst.TAG_DATE_TIME, [None])[0]
        if datetime is not None:
            album_kwargs["date"] = datetime.split("T")[0]
    track_kwargs["date"] = album_kwargs["date"]

    # Clear out any empty values we found
    track_kwargs = {k: v for k, v in track_kwargs.items() if v}
    album_kwargs = {k: v for k, v in album_kwargs.items() if v}

    try:
        # Only bother with album if we have a name to show.
        if album_kwargs.get("name"):
            track_kwargs["album"] = Album(**album_kwargs)

        return Track(
            **track_kwargs,
            uri=uri,
            length=length,
            last_modified=last_modified,
        )
    except ValueError as exc:
        msg = f"Invalid tags: {exc}"
        raise exceptions.ScannerError(msg) from exc


def _artists(
    tags: dict[str, Any],
    artist_name: str,
    artist_id: str | None = None,
    artist_sortname: str | None = None,
) -> list[Artist] | None:
    # Name missing, don't set artist
    if not tags.get(artist_name):
        return None

    # One artist name and either id or sortname, include all available fields
    if len(tags[artist_name]) == 1 and (artist_id in tags or artist_sortname in tags):
        attrs = {"name": tags[artist_name][0]}
        if artist_id in tags:
            attrs["musicbrainz_id"] = tags[artist_id][0]
        if artist_sortname in tags:
            attrs["sortname"] = tags[artist_sortname][0]
        return [Artist(**attrs)]

    # Multiple artist, provide artists with name only to avoid ambiguity.
    return [Artist(name=name) for name in tags[artist_name]]
