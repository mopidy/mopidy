import pytest
from mopidy.models import Album, Artist, Track


def test_uri():
    uri = "an_uri"
    track = Track(uri=uri)
    assert track.uri == uri
    with pytest.raises(AttributeError):
        track.uri = None


def test_name():
    name = "a name"
    track = Track(name=name)
    assert track.name == name
    with pytest.raises(AttributeError):
        track.name = None


def test_artists():
    artists = [Artist(name="name1"), Artist(name="name2")]
    track = Track(artists=artists)
    assert set(track.artists) == set(artists)
    with pytest.raises(AttributeError):
        track.artists = None


def test_composers():
    artists = [Artist(name="name1"), Artist(name="name2")]
    track = Track(composers=artists)
    assert set(track.composers) == set(artists)
    with pytest.raises(AttributeError):
        track.composers = None


def test_performers():
    artists = [Artist(name="name1"), Artist(name="name2")]
    track = Track(performers=artists)
    assert set(track.performers) == set(artists)
    with pytest.raises(AttributeError):
        track.performers = None


def test_album():
    album = Album()
    track = Track(album=album)
    assert track.album == album
    with pytest.raises(AttributeError):
        track.album = None


def test_track_no():
    track_no = 7
    track = Track(track_no=track_no)
    assert track.track_no == track_no
    with pytest.raises(AttributeError):
        track.track_no = None


def test_disc_no():
    disc_no = 2
    track = Track(disc_no=disc_no)
    assert track.disc_no == disc_no
    with pytest.raises(AttributeError):
        track.disc_no = None


def test_date():
    date = "1977-01-01"
    track = Track(date=date)
    assert track.date == date
    with pytest.raises(AttributeError):
        track.date = None


def test_length():
    length = 137000
    track = Track(length=length)
    assert track.length == length
    with pytest.raises(AttributeError):
        track.length = None


def test_bitrate():
    bitrate = 160
    track = Track(bitrate=bitrate)
    assert track.bitrate == bitrate
    with pytest.raises(AttributeError):
        track.bitrate = None


def test_musicbrainz_id():
    mb_id = "mb-id"
    track = Track(musicbrainz_id=mb_id)
    assert track.musicbrainz_id == mb_id
    with pytest.raises(AttributeError):
        track.musicbrainz_id = None


def test_invalid_kwarg():
    with pytest.raises(TypeError):
        Track(foo="baz")


def test_repr_without_artists():
    assert repr(Track(uri="uri", name="name")) == "Track(uri='uri', name='name')"


def test_repr_with_artists():
    assert (
        repr(Track(uri="uri", name="name", artists=frozenset({Artist(name="foo")})))
        == "Track(uri='uri', name='name', artists=frozenset({Artist(name='foo')}))"
    )


def test_serialize_without_artists():
    assert Track(uri="uri", name="name").serialize() == {
        "__model__": "Track",
        "uri": "uri",
        "name": "name",
    }


def test_serialize_with_artists():
    artist = Artist(name="foo")
    assert Track(uri="uri", name="name", artists=[artist]).serialize() == {
        "__model__": "Track",
        "uri": "uri",
        "name": "name",
        "artists": [artist.serialize()],
    }


def test_serialize_with_album():
    album = Album(name="foo")
    assert Track(uri="uri", name="name", album=album).serialize() == {
        "__model__": "Track",
        "uri": "uri",
        "name": "name",
        "album": album.serialize(),
    }
