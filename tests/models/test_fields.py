# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.models.fields import (Boolean, Collection, Field, Identifier,
                                  Integer, String)


def create_instance(field):
    """Create an instance of a dummy class for testing fields."""

    class Dummy(object):
        attr = field
        attr._name = 'attr'

    return Dummy()


class FieldDescriptorTest(unittest.TestCase):
    def test_raw_field_accesible_through_class(self):
        field = Field()
        instance = create_instance(field)
        self.assertEqual(field, instance.__class__.attr)

    def test_field_knows_its_name(self):
        instance = create_instance(Field())
        self.assertEqual('attr', instance.__class__.attr._name)

    def test_field_has_none_as_default(self):
        instance = create_instance(Field())
        self.assertIsNone(instance.attr)

    def test_field_does_not_store_default(self):
        instance = create_instance(Field())
        self.assertFalse(hasattr(instance, '_attr'))

    def test_field_assigment_and_retrival(self):
        instance = create_instance(Field())
        instance.attr = 1234
        self.assertEqual(1234, instance.attr)

    def test_field_can_be_reassigned(self):
        instance = create_instance(Field())
        instance.attr = 1234
        instance.attr = 5678
        self.assertEqual(5678, instance.attr)

    def test_field_can_be_deleted(self):
        instance = create_instance(Field())
        instance.attr = 1234
        del instance.attr
        self.assertEqual(None, instance.attr)
        self.assertFalse(hasattr(instance, '_attr'))

    def test_field_can_be_set_to_none(self):
        instance = create_instance(Field())
        instance.attr = 1234
        instance.attr = None
        self.assertEqual(None, instance.attr)
        self.assertFalse(hasattr(instance, '_attr'))

    def test_field_can_be_set_default(self):
        default = object()
        instance = create_instance(Field(default=default))
        instance.attr = 1234
        instance.attr = default
        self.assertEqual(default, instance.attr)
        self.assertFalse(hasattr(instance, '_attr'))


class FieldTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Field(default=1234))
        self.assertEqual(1234, instance.attr)

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
            create_instance(Field(type=int, default='123'))

    def test_default_respects_choices_check(self):
        with self.assertRaises(TypeError):
            create_instance(Field(choices=(1, 2, 3), default=5))


class StringTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(String(default='abc'))
        self.assertEqual('abc', instance.attr)

    def test_native_str_allowed(self):
        instance = create_instance(String())
        instance.attr = str('abc')
        self.assertEqual('abc', instance.attr)

    def test_bytes_allowed(self):
        instance = create_instance(String())
        instance.attr = b'abc'
        self.assertEqual(b'abc', instance.attr)

    def test_unicode_allowed(self):
        instance = create_instance(String())
        instance.attr = u'abc'
        self.assertEqual(u'abc', instance.attr)

    def test_other_disallowed(self):
        instance = create_instance(String())
        with self.assertRaises(TypeError):
            instance.attr = 1234

    def test_empty_string(self):
        instance = create_instance(String())
        instance.attr = ''
        self.assertEqual('', instance.attr)


class IdentifierTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Identifier(default='abc'))
        self.assertEqual('abc', instance.attr)

    def test_native_str_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = str('abc')
        self.assertEqual('abc', instance.attr)

    def test_bytes_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = b'abc'
        self.assertEqual(b'abc', instance.attr)

    def test_unicode_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = u'abc'
        self.assertEqual(u'abc', instance.attr)

    def test_unicode_with_nonascii_allowed(self):
        instance = create_instance(Identifier())
        instance.attr = u'æøå'
        self.assertEqual(u'æøå'.encode('utf-8'), instance.attr)

    def test_other_disallowed(self):
        instance = create_instance(Identifier())
        with self.assertRaises(TypeError):
            instance.attr = 1234

    def test_empty_string(self):
        instance = create_instance(Identifier())
        instance.attr = ''
        self.assertEqual('', instance.attr)


class IntegerTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Integer(default=1234))
        self.assertEqual(1234, instance.attr)

    def test_int_allowed(self):
        instance = create_instance(Integer())
        instance.attr = int(123)
        self.assertEqual(123, instance.attr)

    def test_long_allowed(self):
        instance = create_instance(Integer())
        instance.attr = long(123)
        self.assertEqual(123, instance.attr)

    def test_float_disallowed(self):
        instance = create_instance(Integer())
        with self.assertRaises(TypeError):
            instance.attr = 123.0

    def test_numeric_string_disallowed(self):
        instance = create_instance(Integer())
        with self.assertRaises(TypeError):
            instance.attr = '123'

    def test_other_disallowed(self):
        instance = create_instance(String())
        with self.assertRaises(TypeError):
            instance.attr = tuple()

    def test_min_validation(self):
        instance = create_instance(Integer(min=0))
        instance.attr = 0
        self.assertEqual(0, instance.attr)

        with self.assertRaises(ValueError):
            instance.attr = -1

    def test_max_validation(self):
        instance = create_instance(Integer(max=10))
        instance.attr = 10
        self.assertEqual(10, instance.attr)

        with self.assertRaises(ValueError):
            instance.attr = 11


class BooleanTest(unittest.TestCase):
    def test_default_handling(self):
        instance = create_instance(Boolean(default=True))
        self.assertEqual(True, instance.attr)

    def test_true_allowed(self):
        instance = create_instance(Boolean())
        instance.attr = True
        self.assertEqual(True, instance.attr)

    def test_false_allowed(self):
        instance = create_instance(Boolean())
        instance.attr = False
        self.assertEqual(False, instance.attr)

    def test_int_forbidden(self):
        instance = create_instance(Boolean())
        with self.assertRaises(TypeError):
            instance.attr = 1


class CollectionTest(unittest.TestCase):
    def test_container_instance_is_default(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        self.assertEqual(frozenset(), instance.attr)

    def test_empty_collection(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        instance.attr = []
        self.assertEqual(frozenset(), instance.attr)

    def test_collection_gets_stored_in_container(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        instance.attr = [1, 2, 3]
        self.assertEqual(frozenset([1, 2, 3]), instance.attr)

    def test_collection_with_wrong_type(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        with self.assertRaises(TypeError):
            instance.attr = [1, '2', 3]

    def test_collection_with_string(self):
        instance = create_instance(Collection(type=int, container=frozenset))
        with self.assertRaises(TypeError):
            instance.attr = '123'

    def test_strings_should_not_be_considered_a_collection(self):
        instance = create_instance(Collection(type=str, container=tuple))
        with self.assertRaises(TypeError):
            instance.attr = b'123'
