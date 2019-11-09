import unittest

from mopidy.models.fields import (
    Boolean,
    Collection,
    Field,
    Identifier,
    Integer,
    String,
)


def create_instance(field):
    """Create an instance of a dummy class for testing fields."""

    class Dummy:
        attr = field
        attr._name = "attr"

    return Dummy()


class FieldDescriptorTest(unittest.TestCase):
    def test_raw_field_accesible_through_class(self):
        field = Field()
        instance = create_instance(field)
        assert field == instance.__class__.attr

    def test_field_knows_its_name(self):
        instance = create_instance(Field())
        assert "attr" == instance.__class__.attr._name

    def test_field_has_none_as_default(self):
        instance = create_instance(Field())
        assert instance.attr is None

    def test_field_does_not_store_default(self):
        instance = create_instance(Field())
        assert not hasattr(instance, "_attr")

    def test_field_assigment_and_retrival(self):
        instance = create_instance(Field())
        instance.attr = 1234
        assert 1234 == instance.attr

    def test_field_can_be_reassigned(self):
        instance = create_instance(Field())
        instance.attr = 1234
        instance.attr = 5678
        assert 5678 == instance.attr

    def test_field_can_be_deleted(self):
        instance = create_instance(Field())
        instance.attr = 1234
        del instance.attr
        assert instance.attr is None
        assert not hasattr(instance, "_attr")

    def test_field_can_be_set_to_none(self):
        instance = create_instance(Field())
        instance.attr = 1234
        instance.attr = None
        assert instance.attr is None
        assert not hasattr(instance, "_attr")

    def test_field_can_be_set_default(self):
        default = object()
        instance = create_instance(Field(default=default))
        instance.attr = 1234
        instance.attr = default
        assert default == instance.attr
        assert not hasattr(instance, "_attr")


class FieldTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Field(default=1234))
        assert 1234 == instance.attr

    def test_type_checking(self):
        instance = create_instance(Field(type=set))
        instance.attr = set()

        with self.assertRaises(TypeError):
            instance.attr = 1234

    def test_choices_checking(self):
        instance = create_instance(Field(choices=(1, 2, 3)))
        instance.attr = 1

        with self.assertRaises(TypeError):
            instance.attr = 4

    def test_default_respects_type_check(self):
        with self.assertRaises(TypeError):
            create_instance(Field(type=int, default="123"))

    def test_default_respects_choices_check(self):
        with self.assertRaises(TypeError):
            create_instance(Field(choices=(1, 2, 3), default=5))


class StringTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(String(default="abc"))
        assert "abc" == instance.attr

    def test_native_str_allowed(self):
        instance = create_instance(String())
        instance.attr = "abc"
        assert "abc" == instance.attr

    def test_unicode_allowed(self):
        instance = create_instance(String())
        instance.attr = "abc"
        assert "abc" == instance.attr

    def test_other_disallowed(self):
        instance = create_instance(String())
        with self.assertRaises(TypeError):
            instance.attr = 1234

    def test_empty_string(self):
        instance = create_instance(String())
        instance.attr = ""
        assert "" == instance.attr


class IdentifierTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Identifier(default="abc"))
        assert "abc" == instance.attr

    def test_native_str_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = "abc"
        assert "abc" == instance.attr

    def test_unicode_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = "abc"
        assert "abc" == instance.attr

    def test_unicode_with_nonascii_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = "æøå"
        assert "æøå" == instance.attr

    def test_other_disallowed(self):
        instance = create_instance(Identifier())
        with self.assertRaises(TypeError):
            instance.attr = 1234

    def test_empty_string(self):
        instance = create_instance(Identifier())
        instance.attr = ""
        assert "" == instance.attr


class IntegerTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Integer(default=1234))
        assert 1234 == instance.attr

    def test_int_allowed(self):
        instance = create_instance(Integer())
        instance.attr = int(123)
        assert 123 == instance.attr

    def test_float_disallowed(self):
        instance = create_instance(Integer())
        with self.assertRaises(TypeError):
            instance.attr = 123.0

    def test_numeric_string_disallowed(self):
        instance = create_instance(Integer())
        with self.assertRaises(TypeError):
            instance.attr = "123"

    def test_other_disallowed(self):
        instance = create_instance(String())
        with self.assertRaises(TypeError):
            instance.attr = tuple()

    def test_min_validation(self):
        instance = create_instance(Integer(min=0))
        instance.attr = 0
        assert 0 == instance.attr

        with self.assertRaises(ValueError):
            instance.attr = -1

    def test_max_validation(self):
        instance = create_instance(Integer(max=10))
        instance.attr = 10
        assert 10 == instance.attr

        with self.assertRaises(ValueError):
            instance.attr = 11


class BooleanTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Boolean(default=True))
        assert instance.attr is True

    def test_true_allowed(self):
        instance = create_instance(Boolean())
        instance.attr = True
        assert instance.attr is True

    def test_false_allowed(self):
        instance = create_instance(Boolean())
        instance.attr = False
        assert instance.attr is False

    def test_int_forbidden(self):
        instance = create_instance(Boolean())
        with self.assertRaises(TypeError):
            instance.attr = 1


class CollectionTest(unittest.TestCase):
    def test_container_instance_is_default(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        assert frozenset() == instance.attr

    def test_empty_collection(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        instance.attr = []
        assert frozenset() == instance.attr

    def test_collection_gets_stored_in_container(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        instance.attr = [1, 2, 3]
        assert frozenset([1, 2, 3]) == instance.attr

    def test_collection_with_wrong_type(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        with self.assertRaises(TypeError):
            instance.attr = [1, "2", 3]

    def test_collection_with_string(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        with self.assertRaises(TypeError):
            instance.attr = "123"

    def test_strings_should_not_be_considered_a_collection(self):
        instance = create_instance(Collection(type=str, container=tuple))
        with self.assertRaises(TypeError):
            instance.attr = b"123"
