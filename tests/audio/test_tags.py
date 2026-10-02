import pytest

from mopidy import exceptions
from mopidy.audio import tags
from mopidy.models import Album, Artist, Track
from mopidy.types import DurationMs, Uri


# TODO: keep ids without name?
# TODO: current test is trying to test everything at once with a complete tags
# set, instead we might want to try with a minimal one making testing easier.
@pytest.fixture
def track_tags():
    return {
        "album": ["album"],
        "track-number": [1],
        "artist": ["artist"],
        "composer": ["composer"],
        "performer": ["performer"],
        "album-artist": ["albumartist"],
        "title": ["track"],
        "track-count": [2],
        "album-disc-number": [2],
        "album-disc-count": [3],
        "date": ["2006-01-01"],
        "container-format": ["ID3 tag"],
        "genre": ["genre"],
        "comment": ["comment"],
        "musicbrainz-trackid": ["a69ac038-02cc-4b2c-8bd2-9ac386faec19"],
        "musicbrainz-albumid": ["00bf7c38-ee81-4efc-9ae7-0e948634143e"],
        "musicbrainz-artistid": ["8760c5ac-ebcb-469f-b01d-ab7c8962ba95"],
        "musicbrainz-sortname": ["sortname"],
        "musicbrainz-albumartistid": ["c1ad4664-81c9-4ea5-b98d-f08ed7362696"],
        "bitrate": [1000],
    }


@pytest.fixture
def track():
    artist = Artist(
        name="artist",
        musicbrainz_id="8760c5ac-ebcb-469f-b01d-ab7c8962ba95",
        sortname="sortname",
    )
    composer = Artist(name="composer")
    performer = Artist(name="performer")
    albumartist = Artist(
        name="albumartist", musicbrainz_id="c1ad4664-81c9-4ea5-b98d-f08ed7362696"
    )

    album = Album(
        name="album",
        date="2006-01-01",
        num_tracks=2,
        num_discs=3,
        musicbrainz_id="00bf7c38-ee81-4efc-9ae7-0e948634143e",
        artists=[albumartist],
    )

    return Track(
        uri=Uri("dummy:track:test"),
        name="track",
        artists=[artist],
        album=album,
        composers=[composer],
        performers=[performer],
        genre="genre",
        track_no=1,
        disc_no=2,
        length=DurationMs(12345),
        date="2006-01-01",
        bitrate=1000,
        comment="comment",
        musicbrainz_id="a69ac038-02cc-4b2c-8bd2-9ac386faec19",
    )


@pytest.fixture
def check(track_tags):
    def check(expected):
        actual = tags.convert_tags_to_track(
            track_tags,
            uri=Uri("dummy:track:test"),
            length=12345,
        )
        assert expected == actual

    return check


def test_convert_tags_to_track_track(check, track):
    check(track)


def test_convert_tags_to_track_missing_track_no(check, track_tags, track):
    del track_tags["track-number"]
    check(track.replace(track_no=None))


def test_convert_tags_to_track_multiple_track_no(check, track_tags, track):
    track_tags["track-number"].append(9)
    check(track)


def test_convert_tags_to_track_missing_track_disc_no(check, track_tags, track):
    del track_tags["album-disc-number"]
    check(track.replace(disc_no=None))


def test_convert_tags_to_track_multiple_track_disc_no(check, track_tags, track):
    track_tags["album-disc-number"].append(9)
    check(track)


def test_convert_tags_to_track_missing_track_name(check, track_tags, track):
    del track_tags["title"]
    check(track.replace(name=None))


def test_convert_tags_to_track_multiple_track_name(check, track_tags, track):
    track_tags["title"] = ["name1", "name2"]
    check(track.replace(name="name1; name2"))


def test_convert_tags_to_track_missing_track_musicbrainz_id(check, track_tags, track):
    del track_tags["musicbrainz-trackid"]
    check(track.replace(musicbrainz_id=None))


def test_convert_tags_to_track_multiple_track_musicbrainz_id(check, track_tags, track):
    track_tags["musicbrainz-trackid"].append("id")
    check(track)


def test_convert_tags_to_track_missing_track_bitrate(check, track_tags, track):
    del track_tags["bitrate"]
    check(track.replace(bitrate=None))


def test_convert_tags_to_track_multiple_track_bitrate(check, track_tags, track):
    track_tags["bitrate"].append(1234)
    check(track)


def test_convert_tags_to_track_missing_track_genre(check, track_tags, track):
    del track_tags["genre"]
    check(track.replace(genre=None))


def test_convert_tags_to_track_multiple_track_genre(check, track_tags, track):
    track_tags["genre"] = ["genre1", "genre2"]
    check(track.replace(genre="genre1; genre2"))


def test_convert_tags_to_track_missing_track_date(check, track_tags, track):
    del track_tags["date"]
    check(
        track.replace(album=track.album.replace(date=None), date=None),
    )


def test_convert_tags_to_track_multiple_track_date(check, track_tags, track):
    track_tags["date"].append("2030-01-01")
    check(track)


def test_convert_tags_to_track_datetime_instead_of_date(check, track_tags, track):
    del track_tags["date"]
    track_tags["datetime"] = ["2006-01-01T14:13:12Z"]
    check(track)


def test_convert_tags_to_track_year_month_datetime_instead_of_date(
    check, track_tags, track
):
    del track_tags["date"]
    track_tags["datetime"] = ["2006-01"]
    check(
        track.replace(
            album=track.album.replace(date="2006-01"),
            date="2006-01",
        ),
    )


def test_convert_tags_to_track_invalid_tags_raises_scanner_error(track_tags, track):
    track_tags["track-number"] = [-1]
    with pytest.raises(exceptions.ScannerError):
        tags.convert_tags_to_track(
            track_tags,
            uri=Uri("dummy:track:test"),
            length=12345,
        )


def test_convert_tags_to_track_missing_track_comment(check, track_tags, track):
    del track_tags["comment"]
    check(track.replace(comment=None))


def test_convert_tags_to_track_multiple_track_comment(check, track_tags, track):
    track_tags["comment"] = ["comment1", "comment2"]
    check(track.replace(comment="comment1; comment2"))


def test_convert_tags_to_track_missing_track_artist_name(check, track_tags, track):
    del track_tags["artist"]
    check(track.replace(artists=frozenset()))


def test_convert_tags_to_track_multiple_track_artist_name(check, track_tags, track):
    track_tags["artist"] = ["name1", "name2"]
    artists = [Artist(name="name1"), Artist(name="name2")]
    check(track.replace(artists=artists))


def test_convert_tags_to_track_missing_track_artist_musicbrainz_id(
    check, track_tags, track
):
    del track_tags["musicbrainz-artistid"]
    artist = next(iter(track.artists)).replace(musicbrainz_id=None)
    check(track.replace(artists=[artist]))


def test_convert_tags_to_track_multiple_track_artist_musicbrainz_id(
    check, track_tags, track
):
    track_tags["musicbrainz-artistid"].append("id")
    check(track)


def test_convert_tags_to_track_missing_track_composer_name(check, track_tags, track):
    del track_tags["composer"]
    check(track.replace(composers=frozenset()))


def test_convert_tags_to_track_multiple_track_composer_name(check, track_tags, track):
    track_tags["composer"] = ["composer1", "composer2"]
    composers = [Artist(name="composer1"), Artist(name="composer2")]
    check(track.replace(composers=composers))


def test_convert_tags_to_track_missing_track_performer_name(check, track_tags, track):
    del track_tags["performer"]
    check(track.replace(performers=frozenset()))


def test_convert_tags_to_track_multiple_track_performe_name(check, track_tags, track):
    track_tags["performer"] = ["performer1", "performer2"]
    performers = [Artist(name="performer1"), Artist(name="performer2")]
    check(track.replace(performers=performers))


def test_convert_tags_to_track_missing_album_name(check, track_tags, track):
    del track_tags["album"]
    check(track.replace(album=None))


def test_convert_tags_to_track_multiple_album_name(check, track_tags, track):
    track_tags["album"].append("album2")
    check(track)


def test_convert_tags_to_track_missing_album_musicbrainz_id(check, track_tags, track):
    del track_tags["musicbrainz-albumid"]
    album = track.album.replace(musicbrainz_id=None)
    check(track.replace(album=album))


def test_convert_tags_to_track_multiple_album_musicbrainz_id(check, track_tags, track):
    track_tags["musicbrainz-albumid"].append("id")
    check(track)


def test_convert_tags_to_track_missing_album_num_tracks(check, track_tags, track):
    del track_tags["track-count"]
    album = track.album.replace(num_tracks=None)
    check(track.replace(album=album))


def test_convert_tags_to_track_multiple_album_num_tracks(check, track_tags, track):
    track_tags["track-count"].append(9)
    check(track)


def test_convert_tags_to_track_missing_album_num_discs(check, track_tags, track):
    del track_tags["album-disc-count"]
    album = track.album.replace(num_discs=None)
    check(track.replace(album=album))


def test_convert_tags_to_track_multiple_album_num_discs(check, track_tags, track):
    track_tags["album-disc-count"].append(9)
    check(track)


def test_convert_tags_to_track_missing_album_artist_name(check, track_tags, track):
    del track_tags["album-artist"]
    album = track.album.replace(artists=frozenset())
    check(track.replace(album=album))


def test_convert_tags_to_track_multiple_album_artist_name(check, track_tags, track):
    track_tags["album-artist"] = ["name1", "name2"]
    artists = [Artist(name="name1"), Artist(name="name2")]
    album = track.album.replace(artists=artists)
    check(track.replace(album=album))


def test_convert_tags_to_track_missing_album_artist_musicbrainz_id(
    check, track_tags, track
):
    del track_tags["musicbrainz-albumartistid"]
    albumartist = next(iter(track.album.artists))
    albumartist = albumartist.replace(musicbrainz_id=None)
    album = track.album.replace(artists=[albumartist])
    check(track.replace(album=album))


def test_convert_tags_to_track_multiple_album_artist_musicbrainz_id(
    check, track_tags, track
):
    track_tags["musicbrainz-albumartistid"].append("id")
    check(track)


def test_convert_tags_to_track_stream_organization_track_name(check, track_tags, track):
    del track_tags["title"]
    track_tags["organization"] = ["organization"]
    check(track.replace(name="organization"))


def test_convert_tags_to_track_multiple_organization_track_name(
    check, track_tags, track
):
    del track_tags["title"]
    track_tags["organization"] = ["organization1", "organization2"]
    check(track.replace(name="organization1; organization2"))


# TODO: combine all comment types?


def test_convert_tags_to_track_stream_location_track_comment(check, track_tags, track):
    del track_tags["comment"]
    track_tags["location"] = ["location"]
    check(track.replace(comment="location"))


def test_convert_tags_to_track_multiple_location_track_comment(
    check, track_tags, track
):
    del track_tags["comment"]
    track_tags["location"] = ["location1", "location2"]
    check(track.replace(comment="location1; location2"))


def test_convert_tags_to_track_stream_copyright_track_comment(check, track_tags, track):
    del track_tags["comment"]
    track_tags["copyright"] = ["copyright"]
    check(track.replace(comment="copyright"))


def test_convert_tags_to_track_multiple_copyright_track_comment(
    check, track_tags, track
):
    del track_tags["comment"]
    track_tags["copyright"] = ["copyright1", "copyright2"]
    check(track.replace(comment="copyright1; copyright2"))


def test_convert_tags_to_track_sortname(check, track_tags, track):
    track_tags["musicbrainz-sortname"] = ["another_sortname"]
    artist = Artist(
        name="artist",
        sortname="another_sortname",
        musicbrainz_id="8760c5ac-ebcb-469f-b01d-ab7c8962ba95",
    )
    check(track.replace(artists=[artist]))


def test_convert_tags_to_track_missing_sortname(check, track_tags, track):
    del track_tags["musicbrainz-sortname"]
    artist = Artist(
        name="artist",
        sortname=None,
        musicbrainz_id="8760c5ac-ebcb-469f-b01d-ab7c8962ba95",
    )
    check(track.replace(artists=[artist]))


def test_convert_tags_to_track_takes_a_length_and_a_last_modified():
    track = tags.convert_tags_to_track(
        {"title": ["a title"]},
        uri=Uri("dummy:uri"),
        length=DurationMs(4704),
        last_modified=1234,
    )

    assert track.length == 4704
    assert track.last_modified == 1234
