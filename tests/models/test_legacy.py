import unittest

import pytest
from mopidy.models import Playlist, Track


class GenericCopyTest(unittest.TestCase):
    def compare(self, orig, other):
        assert orig == other
        assert id(orig) != id(other)

    def test_copying_model(self):
        model = Playlist(uri="foo")
        self.compare(model, model.replace())

    def test_copying_model_with_basic_values(self):
        model = Playlist(name="foo", uri="bar")
        other = model.replace(name="baz")
        assert other.name == "baz"
        assert other.uri == "bar"

    def test_copying_model_with_missing_values(self):
        model = Playlist(uri="bar")
        other = model.replace(name="baz")
        assert other.name == "baz"
        assert other.uri == "bar"

    def test_copying_model_with_private_internal_value(self):
        model = Playlist(uri="uri", tracks=[Track(name=123)])
        other = model.replace(tracks=[Track(name=345)])
        assert Track(name=345) in other.tracks

    def test_copying_model_with_invalid_key(self):
        with pytest.raises(TypeError):
            Playlist().replace(invalid_key=True)

    def test_copying_model_to_remove(self):
        model = Playlist(name="foo").replace(name=None)
        assert model == Playlist()


class ModelTest(unittest.TestCase):
    def test_uri(self):
        uri = "an_uri"
        model = Playlist(uri=uri)
        assert model.uri == uri
        with pytest.raises(AttributeError):
            model.uri = None

    def test_name(self):
        name = "a name"
        model = Playlist(name=name)
        assert model.name == name
        with pytest.raises(AttributeError):
            model.name = None

    def test_submodels(self):
        tracks = (Track(name=123), Track(name=456))
        playlist = Playlist(tracks=tracks)
        assert set(playlist.tracks) == set(tracks)
        with pytest.raises(AttributeError):
            playlist.tracks = None

    def test_models_does_not_validate_data(self):
        assert Playlist(tracks=None).tracks is None  # pyright: ignore[reportArgumentType]

    def test_invalid_kwarg(self):
        with pytest.raises(TypeError):
            Playlist(foo="baz")

    def test_repr_without_models(self):
        assert (
            repr(Playlist(uri="uri", name="name")) == "Playlist(uri='uri', name='name')"
        )

    def test_repr_with_models(self):
        assert (
            repr(Playlist(uri="uri", name="name", tracks=(Track(name=123),)))
            == "Playlist(uri='uri', name='name', tracks=(Track(name=123),))"
        )

    def test_serialize_without_models(self):
        self.assertDictEqual(
            {"__model__": "Playlist", "name": "name", "uri": "uri"},
            Playlist(uri="uri", name="name").serialize(),
        )

    def test_serialize_with_models(self):
        track = Track(name=123)
        self.assertDictEqual(
            {
                "__model__": "Playlist",
                "uri": "uri",
                "name": "name",
                "tracks": (track.serialize(),),
            },
            Playlist(uri="uri", name="name", tracks=(track,)).serialize(),
        )

    def test_eq_uri(self):
        model1 = Playlist(uri="uri1")
        model2 = Playlist(uri="uri1")
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_name(self):
        model1 = Playlist(name="name1")
        model2 = Playlist(name="name1")
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_models(self):
        tracks = (Track(),)
        model1 = Playlist(tracks=tracks)
        model2 = Playlist(tracks=tracks)
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_models_order(self):
        submodel1 = Track(name="name1")
        submodel2 = Track(name="name2")
        model1 = Playlist(tracks=(submodel1, submodel2))
        model2 = Playlist(tracks=(submodel2, submodel1))
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_eq_none(self):
        assert Playlist() is not None

    def test_eq_other(self):
        assert Playlist() != "other"

    def test_ne_uri(self):
        model1 = Playlist(uri="uri1")
        model2 = Playlist(uri="uri2")
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_ne_name(self):
        model1 = Playlist(name="name1")
        model2 = Playlist(name="name2")
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_ne_models(self):
        model1 = Playlist(tracks=(Track(name="name1"),))
        model2 = Playlist(tracks=(Track(name="name2"),))
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_ignores_values_with_default_value_none(self):
        model1 = Playlist(name="name1")
        model2 = Playlist(name="name1", uri=None)
        assert model1 == model2
        assert hash(model1) == hash(model2)
