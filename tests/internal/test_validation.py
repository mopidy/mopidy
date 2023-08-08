import pytest

from mopidy import exceptions
from mopidy.internal import validation


def test_check_boolean_with_valid_values():
    for value in (True, False):
        validation.check_boolean(value)


def test_check_boolean_with_other_values():
    for value in 1, 0, None, "", [], ():
        with pytest.raises(exceptions.ValidationError):
            validation.check_boolean(value)


def test_check_boolean_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_boolean(1234)
    assert str(excinfo.value) == "Expected a boolean, not 1234"


def test_check_choice_with_valid_values():
    for value, choices in (2, (1, 2, 3)), ("abc", ("abc", "def")):
        validation.check_choice(value, choices)


def test_check_choice_with_invalid_values():
    for value, choices in (5, (1, 2, 3)), ("xyz", ("abc", "def")):
        with pytest.raises(exceptions.ValidationError):
            validation.check_choice(value, choices)


def test_check_choice_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_choice(5, (1, 2, 3))
    assert str(excinfo.value) == "Expected one of (1, 2, 3), not 5"


def test_check_instance_with_valid_choices():
    for value, cls in ((True, bool), ("a", str), (123, int)):
        validation.check_instance(value, cls)


def test_check_instance_with_invalid_values():
    for value, cls in (1, str), ("abc", int):
        with pytest.raises(exceptions.ValidationError):
            validation.check_instance(value, cls)


def test_check_instance_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_instance(1, dict)
    assert str(excinfo.value) == "Expected a dict instance, not 1"


def test_check_instances_with_valid_values():
    validation.check_instances([], int)
    validation.check_instances([1, 2], int)
    validation.check_instances((1, 2), int)


def test_check_instances_with_invalid_values():
    with pytest.raises(exceptions.ValidationError):
        validation.check_instances("abc", str)
    with pytest.raises(exceptions.ValidationError):
        validation.check_instances(["abc", 123], str)
    with pytest.raises(exceptions.ValidationError):
        validation.check_instances(None, str)
    with pytest.raises(exceptions.ValidationError):
        validation.check_instances([None], str)
    with pytest.raises(exceptions.ValidationError):
        validation.check_instances(iter(["abc"]), str)


def test_check_instances_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_instances([1], str)
    assert str(excinfo.value) == "Expected a list of str, not [1]"


def test_check_query_valid_values():
    for value in {}, {"any": []}, {"any": ["abc"]}:
        validation.check_query(value)


def test_check_query_random_iterables():
    for value in None, (), [], "abc":
        with pytest.raises(exceptions.ValidationError):
            validation.check_query(value)


def test_check_mapping_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_query([])
    assert str(excinfo.value) == "Expected a query dictionary, not []"


def test_check_query_invalid_fields():
    for value in "wrong", "bar", "foo", "tlid":
        with pytest.raises(exceptions.ValidationError):
            validation.check_query({value: []})


def test_check_field_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_query({"wrong": ["abc"]})
    assert "Expected query field to be one of " in str(excinfo.value)


def test_check_query_invalid_values():
    for value in "", None, "foo", 123, [""], [None], iter(["abc"]):
        with pytest.raises(exceptions.ValidationError):
            validation.check_query({"any": value})


def test_check_values_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_query({"any": "abc"})
    assert 'Expected "any" to be list of strings, not' in str(excinfo.value)


def test_check_uri_with_valid_values():
    for value in "foobar:", "http://example.com", "git+http://example.com":
        validation.check_uri(value)


def test_check_uri_with_invalid_values():
    # Note that tuple catches a potential bug with using "'foo' % arg" for
    # formatting.
    for value in ("foobar", "htt p://example.com", None, 1234, ()):
        with pytest.raises(exceptions.ValidationError):
            validation.check_uri(value)


def test_check_uri_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_uri("testing")
    assert str(excinfo.value) == "Expected a valid URI, not 'testing'"


def test_check_uris_with_valid_values():
    validation.check_uris([])
    validation.check_uris(["foobar:"])
    validation.check_uris(("foobar:",))


def test_check_uris_with_invalid_values():
    with pytest.raises(exceptions.ValidationError):
        validation.check_uris("foobar:")
    with pytest.raises(exceptions.ValidationError):
        validation.check_uris(None)
    with pytest.raises(exceptions.ValidationError):
        validation.check_uris([None])
    with pytest.raises(exceptions.ValidationError):
        validation.check_uris(["foobar:", "foobar"])
    with pytest.raises(exceptions.ValidationError):
        validation.check_uris(iter(["http://example.com"]))


def test_check_uris_error_message():
    with pytest.raises(exceptions.ValidationError) as excinfo:
        validation.check_uris("testing")
    assert str(excinfo.value) == "Expected a list of URIs, not 'testing'"
