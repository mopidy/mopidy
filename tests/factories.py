from faker import Faker
from polyfactory import PostGenerated, Use
from polyfactory.factories.pydantic_factory import ModelFactory

from mopidy.models import (
    Album,
    Artist,
    Image,
    ModelType,
    Playlist,
    Ref,
    SearchResult,
    TlTrack,
    Track,
)

faker = Faker(locale="en_US")


def fake_date(faker: Faker) -> str:
    date = faker.date_between(start_date="-75y", end_date="today")
    if faker.random.randint(0, 3) == 0:
        return str(date.year)  # Return just the year 25% of the time
    return date.strftime("%Y-%m-%d")


class ImageFactory(ModelFactory[Image]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    uri: str = PostGenerated(
        lambda field, values: faker.image_url(
            width=values["width"],
            height=values["height"],
        )
    )
    width = Use(faker.random.randint, a=100, b=2000)
    height = Use(faker.random.randint, a=100, b=2000)


class ArtistFactory(ModelFactory[Artist]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    uri = Use(faker.lexify, text="dummy:artist:????")
    name = Use(faker.name)
    sortname = PostGenerated(lambda field, values: values["name"])
    musicbrainz_id = None


class AlbumFactory(ModelFactory[Album]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    uri = Use(faker.lexify, text="dummy:album:????")
    name = Use(faker.sentence, nb_words=3)
    artists = Use(ArtistFactory.batch, size=1)
    num_tracks = Use(faker.random.randint, a=5, b=20)
    num_discs = Use(faker.random.randint, a=1, b=2)
    date = Use(fake_date, faker)
    musicbrainz_id = None


class TrackFactory(ModelFactory[Track]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    uri = Use(faker.lexify, text="dummy:track:????")
    name = Use(faker.sentence, nb_words=3)
    artists = Use(ArtistFactory.batch, size=1)
    album = AlbumFactory
    composers = Use(ArtistFactory.batch, size=0)
    performers = Use(ArtistFactory.batch, size=0)
    genre = Use(faker.random.choice, seq=[None, "Rock", "Pop", "Jazz", "Classical"])
    track_no = Use(faker.random.randint, a=1, b=20)
    disc_no = Use(faker.random.randint, a=1, b=2)
    date = Use(fake_date, faker)
    length = Use(faker.random.randint, a=25_000, b=500_000)
    bitrate = Use(faker.random.choice, seq=[None, 128, 192, 256, 320])
    comment = Use(faker.sentence, nb_words=4)
    musicbrainz_id = None


class PlaylistFactory(ModelFactory[Playlist]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    uri = Use(faker.lexify, text="dummy:playlist:????")
    name = Use(faker.sentence, nb_words=2)
    tracks = Use(TrackFactory.batch, size=5)


class SearchResultFactory(ModelFactory[SearchResult]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    uri = Use(faker.lexify, text="dummy:search:????")
    tracks = Use(TrackFactory.batch, size=5)
    artists = Use(ArtistFactory.batch, size=3)
    albums = Use(AlbumFactory.batch, size=2)


class TlTrackFactory(ModelFactory[TlTrack]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    tlid: int = Use(faker.random.randint, a=1, b=10_000)
    track = TrackFactory


class RefFactory(ModelFactory[Ref]):
    __set_as_default_factory_for_type__ = True
    __faker__ = faker

    type = Use(faker.enum, ModelType)
    uri = PostGenerated(
        lambda field, values: faker.lexify(text=f"dummy:{values['type']}:????")
    )
    name = PostGenerated(
        lambda field, values: (
            faker.name()
            if values["type"] == ModelType.ARTIST
            else faker.sentence(nb_words=3)
        )
    )
