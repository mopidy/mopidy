import unittest

from mopidy.models import ImmutableObject


class Model(ImmutableObject):
    uri = None
    name = None
    models = frozenset()

    def __init__(self, *args, **kwargs):
        self.__dict__["models"] = frozenset(kwargs.pop("models", None) or [])
        super().__init__(self, *args, **kwargs)


class SubModel(ImmutableObject):
    uri = None
    name = None


class GenericCopyTest(unittest.TestCase):
    def compare(self, orig, other):
        assert orig == other
        assert id(orig) != id(other)

    def test_copying_model(self):
        model = Model()
        self.compare(model, model.replace())

    def test_copying_model_with_basic_values(self):
        model = Model(name="foo", uri="bar")
        other = model.replace(name="baz")
        assert "baz" == other.name
        assert "bar" == other.uri

    def test_copying_model_with_missing_values(self):
        model = Model(uri="bar")
        other = model.replace(name="baz")
        assert "baz" == other.name
        assert "bar" == other.uri

    def test_copying_model_with_private_internal_value(self):
        model = Model(models=[SubModel(name=123)])
        other = model.replace(models=[SubModel(name=345)])
        assert SubModel(name=345) in other.models

    def test_copying_model_with_invalid_key(self):
        with self.assertRaises(TypeError):
            Model().replace(invalid_key=True)

    def test_copying_model_to_remove(self):
        model = Model(name="foo").replace(name=None)
        assert model == Model()


class ModelTest(unittest.TestCase):
    def test_uri(self):
        uri = "an_uri"
        model = Model(uri=uri)
        assert model.uri == uri
        with self.assertRaises(AttributeError):
            model.uri = None

    def test_name(self):
        name = "a name"
        model = Model(name=name)
        assert model.name == name
        with self.assertRaises(AttributeError):
            model.name = None

    def test_submodels(self):
        models = [SubModel(name=123), SubModel(name=456)]
        model = Model(models=models)
        assert set(model.models) == set(models)
        with self.assertRaises(AttributeError):
            model.models = None

    def test_models_none(self):
        assert set() == Model(models=None).models

    def test_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            Model(foo="baz")

    def test_repr_without_models(self):
        assert "Model(name='name', uri='uri')" == repr(
            Model(uri="uri", name="name")
        )

    def test_repr_with_models(self):
        assert (
            "Model(models=[SubModel(name=123)], name='name', uri='uri')"
            == repr(Model(uri="uri", name="name", models=[SubModel(name=123)]))
        )

    def test_serialize_without_models(self):
        self.assertDictEqual(
            {"__model__": "Model", "uri": "uri", "name": "name"},
            Model(uri="uri", name="name").serialize(),
        )

    def test_serialize_with_models(self):
        submodel = SubModel(name=123)
        self.assertDictEqual(
            {
                "__model__": "Model",
                "uri": "uri",
                "name": "name",
                "models": [submodel.serialize()],
            },
            Model(uri="uri", name="name", models=[submodel]).serialize(),
        )

    def test_eq_uri(self):
        model1 = Model(uri="uri1")
        model2 = Model(uri="uri1")
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_name(self):
        model1 = Model(name="name1")
        model2 = Model(name="name1")
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_models(self):
        models = [SubModel()]
        model1 = Model(models=models)
        model2 = Model(models=models)
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_models_order(self):
        submodel1 = SubModel(name="name1")
        submodel2 = SubModel(name="name2")
        model1 = Model(models=[submodel1, submodel2])
        model2 = Model(models=[submodel2, submodel1])
        assert model1 == model2
        assert hash(model1) == hash(model2)

    def test_eq_none(self):
        assert Model() is not None

    def test_eq_other(self):
        assert Model() != "other"

    def test_ne_uri(self):
        model1 = Model(uri="uri1")
        model2 = Model(uri="uri2")
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_ne_name(self):
        model1 = Model(name="name1")
        model2 = Model(name="name2")
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_ne_models(self):
        model1 = Model(models=[SubModel(name="name1")])
        model2 = Model(models=[SubModel(name="name2")])
        assert model1 != model2
        assert hash(model1) != hash(model2)

    def test_ignores_values_with_default_value_none(self):
        model1 = Model(name="name1")
        model2 = Model(name="name1", uri=None)
        assert model1 == model2
        assert hash(model1) == hash(model2)
