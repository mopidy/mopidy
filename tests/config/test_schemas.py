import logging
from unittest import mock

import pytest
from dirty_equals import IsStr

from mopidy.config import schemas, types


@pytest.fixture
def schema():
    schema = schemas.ConfigSchema("test")
    schema["foo"] = mock.Mock()
    schema["bar"] = mock.Mock()
    schema["baz"] = mock.Mock()
    return schema


@pytest.fixture
def values():
    return {"bar": "123", "foo": "456", "baz": "678"}


def test_config_schema_deserialize(schema, values):
    schema.deserialize(values)


def test_config_schema_deserialize_with_missing_value(schema, values):
    del values["foo"]

    result, errors = schema.deserialize(values)
    assert errors == {"foo": IsStr}
    assert result.pop("foo") is None
    assert result.pop("bar") is not None
    assert result.pop("baz") is not None
    assert result == {}


def test_config_schema_deserialize_with_extra_value(schema, values):
    values["extra"] = "123"

    result, errors = schema.deserialize(values)
    assert errors == {"extra": IsStr}
    assert result.pop("foo") is not None
    assert result.pop("bar") is not None
    assert result.pop("baz") is not None
    assert result == {}


def test_config_schema_deserialize_with_deserialization_error(schema, values):
    schema["foo"].deserialize.side_effect = ValueError("failure")

    result, errors = schema.deserialize(values)
    assert errors == {"foo": "failure"}
    assert result.pop("foo") is None
    assert result.pop("bar") is not None
    assert result.pop("baz") is not None
    assert result == {}


def test_config_schema_deserialize_with_multiple_deserialization_errors(schema, values):
    schema["foo"].deserialize.side_effect = ValueError("failure")
    schema["bar"].deserialize.side_effect = ValueError("other")

    result, errors = schema.deserialize(values)
    assert errors == {"foo": "failure", "bar": "other"}
    assert result.pop("foo") is None
    assert result.pop("bar") is None
    assert result.pop("baz") is not None
    assert result == {}


def test_config_schema_deserialize_deserialization_unknown_and_missing_errors(
    schema, values
):
    values["extra"] = "123"
    schema["bar"].deserialize.side_effect = ValueError("failure")
    del values["baz"]

    result, errors = schema.deserialize(values)
    assert "unknown" in errors["extra"]
    assert "foo" not in errors
    assert "failure" in errors["bar"]
    assert "not found" in errors["baz"]

    assert "unknown" not in result
    assert "foo" in result
    assert result["bar"] is None
    assert result["baz"] is None


def test_config_schema_deserialize_deprecated_value(schema, values):
    schema["foo"] = types.Deprecated()

    result, errors = schema.deserialize(values)
    assert sorted(result.keys()) == ["bar", "baz"]
    assert "foo" not in errors


def test_map_config_schema_conversion():
    schema = schemas.MapConfigSchema("test", types.LogLevel())
    result, errors = schema.deserialize({"foo.bar": "DEBUG", "baz": "INFO"})

    assert result["foo.bar"] == logging.DEBUG
    assert result["baz"] == logging.INFO
    assert not errors


def test_did_you_mean_suggestions():
    choices = ("enabled", "username", "password", "bitrate", "timeout")

    suggestion = schemas._did_you_mean("bitrate", choices)
    assert suggestion == "bitrate"

    suggestion = schemas._did_you_mean("bitrote", choices)
    assert suggestion == "bitrate"

    suggestion = schemas._did_you_mean("Bitrot", choices)
    assert suggestion == "bitrate"

    suggestion = schemas._did_you_mean("BTROT", choices)
    assert suggestion == "bitrate"

    suggestion = schemas._did_you_mean("btro", choices)
    assert suggestion is None
