import logging
import unittest
from unittest import mock

from mopidy.config import schemas, types

from tests import any_unicode


class ConfigSchemaTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.schema = schemas.ConfigSchema("test")
        self.schema["foo"] = mock.Mock()
        self.schema["bar"] = mock.Mock()
        self.schema["baz"] = mock.Mock()
        self.values = {"bar": "123", "foo": "456", "baz": "678"}

    def test_deserialize(self):
        self.schema.deserialize(self.values)

    def test_deserialize_with_missing_value(self):
        del self.values["foo"]

        result, errors = self.schema.deserialize(self.values)
        assert {"foo": any_unicode} == errors
        assert result.pop("foo") is None
        assert result.pop("bar") is not None
        assert result.pop("baz") is not None
        assert {} == result

    def test_deserialize_with_extra_value(self):
        self.values["extra"] = "123"

        result, errors = self.schema.deserialize(self.values)
        assert {"extra": any_unicode} == errors
        assert result.pop("foo") is not None
        assert result.pop("bar") is not None
        assert result.pop("baz") is not None
        assert {} == result

    def test_deserialize_with_deserialization_error(self):
        self.schema["foo"].deserialize.side_effect = ValueError("failure")

        result, errors = self.schema.deserialize(self.values)
        assert {"foo": "failure"} == errors
        assert result.pop("foo") is None
        assert result.pop("bar") is not None
        assert result.pop("baz") is not None
        assert {} == result

    def test_deserialize_with_multiple_deserialization_errors(self):
        self.schema["foo"].deserialize.side_effect = ValueError("failure")
        self.schema["bar"].deserialize.side_effect = ValueError("other")

        result, errors = self.schema.deserialize(self.values)
        assert {"foo": "failure", "bar": "other"} == errors
        assert result.pop("foo") is None
        assert result.pop("bar") is None
        assert result.pop("baz") is not None
        assert {} == result

    def test_deserialize_deserialization_unknown_and_missing_errors(self):
        self.values["extra"] = "123"
        self.schema["bar"].deserialize.side_effect = ValueError("failure")
        del self.values["baz"]

        result, errors = self.schema.deserialize(self.values)
        assert "unknown" in errors["extra"]
        assert "foo" not in errors
        assert "failure" in errors["bar"]
        assert "not found" in errors["baz"]

        assert "unknown" not in result
        assert "foo" in result
        assert result["bar"] is None
        assert result["baz"] is None

    def test_deserialize_deprecated_value(self):
        self.schema["foo"] = types.Deprecated()

        result, errors = self.schema.deserialize(self.values)
        assert ["bar", "baz"] == sorted(result.keys())
        assert "foo" not in errors


class MapConfigSchemaTest(unittest.TestCase):
    def test_conversion(self):
        schema = schemas.MapConfigSchema("test", types.LogLevel())
        result, errors = schema.deserialize({"foo.bar": "DEBUG", "baz": "INFO"})

        assert logging.DEBUG == result["foo.bar"]
        assert logging.INFO == result["baz"]


class DidYouMeanTest(unittest.TestCase):
    def test_suggestions(self):
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
