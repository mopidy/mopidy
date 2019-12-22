import logging
import socket
from unittest import mock

import pytest

from mopidy.config import types
from mopidy.internal import log


@pytest.mark.parametrize(
    "value, expected",
    [
        # bytes are coded from UTF-8 and string-escaped:
        (b"abc", "abc"),
        ("æøå".encode(), "æøå"),
        (b"a\nb", "a\nb"),
        (b"a\\nb", "a\nb"),
        # unicode strings are string-escaped:
        ("abc", "abc"),
        ("æøå", "æøå"),
        ("a\nb", "a\nb"),
        ("a\\nb", "a\nb"),
    ],
)
def test_decode(value, expected):
    assert types.decode(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        # unicode strings are string-escaped and encoded as UTF-8:
        ("abc", "abc"),
        ("æøå", "æøå"),
        ("a\nb", "a\\nb"),
        # bytes are string-escaped:
        (b"abc", "abc"),
        (b"a\nb", "a\\nb"),
    ],
)
def test_encode(value, expected):
    assert types.encode(value) == expected


def test_encode_decode_invalid_utf8():
    data = b"\xc3\x00"  # invalid utf-8

    result = types.encode(types.decode(data))

    assert isinstance(result, str)
    assert result == data.decode(errors="surrogateescape")


class TestConfigValue:
    def test_deserialize_decodes_bytes(self):
        cv = types.ConfigValue()

        result = cv.deserialize(b"abc")

        assert isinstance(result, str)

    def test_serialize_conversion_to_string(self):
        cv = types.ConfigValue()

        result = cv.serialize(object())

        assert isinstance(result, str)

    def test_serialize_none(self):
        cv = types.ConfigValue()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == ""

    def test_serialize_supports_display(self):
        cv = types.ConfigValue()

        result = cv.serialize(object(), display=True)

        assert isinstance(result, str)


class TestDeprecated:
    def test_deserialize_returns_deprecated_value(self):
        cv = types.Deprecated()

        result = cv.deserialize(b"foobar")

        assert isinstance(result, types.DeprecatedValue)

    def test_serialize_returns_deprecated_value(self):
        cv = types.Deprecated()

        result = cv.serialize("foobar")

        assert isinstance(result, types.DeprecatedValue)


class TestString:
    def test_deserialize_conversion_success(self):
        cv = types.String()

        result = cv.deserialize(b" foo ")

        assert result == "foo"
        assert isinstance(result, str)

    def test_deserialize_decodes_utf8(self):
        cv = types.String()

        result = cv.deserialize("æøå".encode())

        assert result == "æøå"

    def test_deserialize_does_not_double_encode_unicode(self):
        cv = types.String()

        result = cv.deserialize("æøå")

        assert result == "æøå"

    def test_deserialize_handles_escapes(self):
        cv = types.String(optional=True)

        result = cv.deserialize(b"a\\t\\nb")

        assert result == "a\t\nb"

    def test_deserialize_enforces_choices(self):
        cv = types.String(choices=["foo", "bar", "baz"])

        assert cv.deserialize(b"foo") == "foo"

        with pytest.raises(ValueError):
            cv.deserialize(b"foobar")

    def test_deserialize_enforces_required(self):
        cv = types.String()

        with pytest.raises(ValueError):
            cv.deserialize(b"")

    def test_deserialize_respects_optional(self):
        cv = types.String(optional=True)

        assert cv.deserialize(b"") is None
        assert cv.deserialize(b" ") is None

    def test_deserialize_invalid_encoding(self):
        cv = types.String()
        incorrectly_encoded_bytes = "æøå".encode("iso-8859-1")

        assert cv.deserialize(incorrectly_encoded_bytes) == "\udce6\udcf8\udce5"

    def test_serialize_returns_text(self):
        cv = types.String()

        result = cv.serialize("æøå")

        assert isinstance(result, str)
        assert result == "æøå"

    def test_serialize_decodes_bytes(self):
        cv = types.String()
        bytes_string = "æøå".encode()

        result = cv.serialize(bytes_string)

        assert isinstance(result, str)
        assert result == bytes_string.decode()

    def test_serialize_handles_escapes(self):
        cv = types.String()

        result = cv.serialize("a\n\tb")

        assert isinstance(result, str)
        assert result == r"a\n\tb"

    def test_serialize_none(self):
        cv = types.String()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == ""

    def test_deserialize_enforces_choices_optional(self):
        cv = types.String(optional=True, choices=["foo", "bar", "baz"])

        assert cv.deserialize(b"") is None

        with pytest.raises(ValueError):
            cv.deserialize(b"foobar")


class TestSecret:
    def test_deserialize_decodes_utf8(self):
        cv = types.Secret()

        result = cv.deserialize("æøå".encode())

        assert isinstance(result, str)
        assert result == "æøå"

    def test_deserialize_enforces_required(self):
        cv = types.Secret()

        with pytest.raises(ValueError):
            cv.deserialize(b"")

    def test_deserialize_respects_optional(self):
        cv = types.Secret(optional=True)

        assert cv.deserialize(b"") is None
        assert cv.deserialize(b" ") is None

    def test_serialize_none(self):
        cv = types.Secret()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == ""

    def test_serialize_for_display_masks_value(self):
        cv = types.Secret()

        result = cv.serialize("s3cret", display=True)

        assert isinstance(result, str)
        assert result == "********"

    def test_serialize_none_for_display(self):
        cv = types.Secret()

        result = cv.serialize(None, display=True)

        assert isinstance(result, str)
        assert result == ""


class TestInteger:
    def test_deserialize_conversion_success(self):
        cv = types.Integer()

        assert cv.deserialize("123") == 123
        assert cv.deserialize("0") == 0
        assert cv.deserialize("-10") == -10

    def test_deserialize_conversion_failure(self):
        cv = types.Integer()

        with pytest.raises(ValueError):
            cv.deserialize("asd")

        with pytest.raises(ValueError):
            cv.deserialize("3.14")

    def test_deserialize_enforces_required(self):
        cv = types.Integer()

        with pytest.raises(ValueError):
            cv.deserialize("")

    def test_deserialize_respects_optional(self):
        cv = types.Integer(optional=True)

        assert cv.deserialize("") is None

    def test_deserialize_enforces_choices(self):
        cv = types.Integer(choices=[1, 2, 3])

        cv.deserialize("3") == 3

        with pytest.raises(ValueError):
            cv.deserialize("5")

    def test_deserialize_enforces_minimum(self):
        cv = types.Integer(minimum=10)

        assert cv.deserialize("15") == 15

        with pytest.raises(ValueError):
            cv.deserialize("5")

    def test_deserialize_enforces_maximum(self):
        cv = types.Integer(maximum=10)

        assert cv.deserialize("5") == 5

        with pytest.raises(ValueError):
            cv.deserialize("15")


class TestBoolean:
    def test_deserialize_conversion_success(self):
        cv = types.Boolean()

        for true in ("1", "yes", "true", "on"):
            assert cv.deserialize(true) is True
            assert cv.deserialize(true.upper()) is True
            assert cv.deserialize(true.capitalize()) is True

        for false in ("0", "no", "false", "off"):
            assert cv.deserialize(false) is False
            assert cv.deserialize(false.upper()) is False
            assert cv.deserialize(false.capitalize()) is False

    def test_deserialize_conversion_failure(self):
        cv = types.Boolean()

        with pytest.raises(ValueError):
            cv.deserialize("nope")

        with pytest.raises(ValueError):
            cv.deserialize("sure")

    def test_deserialize_enforces_required(self):
        cv = types.Boolean()

        with pytest.raises(ValueError):
            cv.deserialize("")

    def test_deserialize_respects_optional(self):
        cv = types.Boolean(optional=True)

        assert cv.deserialize("") is None

    def test_serialize_true(self):
        cv = types.Boolean()

        result = cv.serialize(True)

        assert isinstance(result, str)
        assert result == "true"

    def test_serialize_false(self):
        cv = types.Boolean()

        result = cv.serialize(False)

        assert isinstance(result, str)
        assert result == "false"

    def test_serialize_none_as_false(self):
        # TODO We should consider making `None` an invalid value, but we have
        # existing code that assumes it to work like False.

        cv = types.Boolean()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == "false"

    def test_serialize_invalid_values(self):
        cv = types.Boolean()

        with pytest.raises(ValueError):
            cv.serialize([])

        with pytest.raises(ValueError):
            cv.serialize("1")


class TestList:
    # TODO: add test_deserialize_ignores_blank
    # TODO: add test_serialize_ignores_blank
    # TODO: add test_deserialize_handles_escapes

    def test_deserialize_conversion_success(self):
        cv = types.List()

        result = cv.deserialize(b"foo, bar ,baz ")
        assert result == ("foo", "bar", "baz")

        result = cv.deserialize(b" foo,bar\nbar\nbaz")
        assert result == ("foo,bar", "bar", "baz")

    def test_deserialize_creates_tuples(self):
        cv = types.List(optional=True)

        assert isinstance(cv.deserialize(b"foo,bar,baz"), tuple)
        assert isinstance(cv.deserialize(b""), tuple)

    def test_deserialize_decodes_utf8(self):
        cv = types.List()

        result = cv.deserialize("æ, ø, å".encode())
        assert result == ("æ", "ø", "å")

        result = cv.deserialize("æ\nø\nå".encode())
        assert result == ("æ", "ø", "å")

    def test_deserialize_does_not_double_encode_unicode(self):
        cv = types.List()

        result = cv.deserialize("æ, ø, å")
        assert result == ("æ", "ø", "å")

        result = cv.deserialize("æ\nø\nå")
        assert result == ("æ", "ø", "å")

    def test_deserialize_enforces_required(self):
        cv = types.List()

        with pytest.raises(ValueError):
            cv.deserialize(b"")

    def test_deserialize_respects_optional(self):
        cv = types.List(optional=True)

        assert cv.deserialize(b"") == ()

    def test_serialize(self):
        cv = types.List()

        result = cv.serialize(("foo", "bar", "baz"))

        assert isinstance(result, str)
        assert result == "\n  foo\n  bar\n  baz"

    def test_serialize_none(self):
        cv = types.List()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == ""


class TestLogColor:
    def test_deserialize(self):
        cv = types.LogColor()

        assert cv.deserialize(b"RED") == "red"
        assert cv.deserialize("RED") == "red"
        assert cv.deserialize(b"red") == "red"
        assert cv.deserialize("red") == "red"

    def test_deserialize_enforces_choices(self):
        cv = types.LogColor()

        with pytest.raises(ValueError):
            cv.deserialize("golden")

    def test_serialize(self):
        cv = types.LogColor()

        assert cv.serialize("red") == "red"
        assert cv.serialize("blue") == "blue"

    def test_serialize_ignores_unknown_color(self):
        cv = types.LogColor()

        assert cv.serialize("golden") == ""


class TestLogLevel:
    levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "trace": log.TRACE_LOG_LEVEL,
        "all": logging.NOTSET,
    }

    def test_deserialize_conversion_success(self):
        cv = types.LogLevel()

        for name, level in self.levels.items():
            assert cv.deserialize(name) == level
            assert cv.deserialize(name.upper()) == level
            assert cv.deserialize(name.capitalize()) == level

    def test_deserialize_conversion_failure(self):
        cv = types.LogLevel()

        with pytest.raises(ValueError):
            cv.deserialize("red alert")

        with pytest.raises(ValueError):
            cv.deserialize(" ")

    def test_serialize(self):
        cv = types.LogLevel()

        for name, level in self.levels.items():
            cv.serialize(level) == name

    def test_serialize_ignores_unknown_level(self):
        cv = types.LogLevel()

        assert cv.serialize(1337) == ""


class TestHostname:
    @mock.patch("socket.getaddrinfo")
    def test_deserialize_conversion_success(self, getaddrinfo_mock):
        cv = types.Hostname()

        cv.deserialize("example.com")

        getaddrinfo_mock.assert_called_once_with("example.com", None)

    @mock.patch("socket.getaddrinfo")
    def test_deserialize_conversion_failure(self, getaddrinfo_mock):
        cv = types.Hostname()
        getaddrinfo_mock.side_effect = socket.error

        with pytest.raises(ValueError):
            cv.deserialize("example.com")

    @mock.patch("socket.getaddrinfo")
    def test_deserialize_enforces_required(self, getaddrinfo_mock):
        cv = types.Hostname()

        with pytest.raises(ValueError):
            cv.deserialize("")

        with pytest.raises(ValueError):
            cv.deserialize(" ")

        assert getaddrinfo_mock.call_count == 0

    @mock.patch("socket.getaddrinfo")
    def test_deserialize_respects_optional(self, getaddrinfo_mock):
        cv = types.Hostname(optional=True)

        assert cv.deserialize("") is None
        assert cv.deserialize(" ") is None
        assert getaddrinfo_mock.call_count == 0

    @mock.patch("mopidy.internal.path.expand_path")
    def test_deserialize_with_unix_socket(self, expand_path_mock):
        cv = types.Hostname()

        assert cv.deserialize("unix:/tmp/mopidy.socket") is not None
        expand_path_mock.assert_called_once_with("/tmp/mopidy.socket")


class TestPort:
    def test_valid_ports(self):
        cv = types.Port()

        assert cv.deserialize("0") == 0
        assert cv.deserialize("1") == 1
        assert cv.deserialize("80") == 80
        assert cv.deserialize("6600") == 6600
        assert cv.deserialize("65535") == 65535

    def test_invalid_ports(self):
        cv = types.Port()

        with pytest.raises(ValueError):
            cv.deserialize("65536")

        with pytest.raises(ValueError):
            cv.deserialize("100000")

        with pytest.raises(ValueError):
            cv.deserialize("-1")

        with pytest.raises(ValueError):
            cv.deserialize("")


class TestExpandedPath:
    def test_is_str(self):
        assert isinstance(types._ExpandedPath(b"/tmp", b"foo"), str)

    def test_stores_both_expanded_and_original_path(self):
        original = "~"
        expanded = "expanded_path"

        result = types._ExpandedPath(original, expanded)

        assert result == expanded
        assert result.original == original


class TestPath:
    def test_deserialize_conversion_success(self):
        cv = types.Path()

        result = cv.deserialize(b"/foo")

        assert result == "/foo"
        assert isinstance(result, types._ExpandedPath)
        assert isinstance(result, str)

    def test_deserialize_enforces_required(self):
        cv = types.Path()

        with pytest.raises(ValueError):
            cv.deserialize(b"")

    def test_deserialize_respects_optional(self):
        cv = types.Path(optional=True)

        assert cv.deserialize(b"") is None
        assert cv.deserialize(b" ") is None

    def test_serialize_uses_original(self):
        cv = types.Path()
        path = types._ExpandedPath("original_path", "expanded_path")

        assert cv.serialize(path) == "original_path"

    def test_serialize_plain_string(self):
        cv = types.Path()

        assert cv.serialize(b"path") == "path"

    def test_serialize_supports_unicode_string(self):
        cv = types.Path()

        assert cv.serialize("æøå") == "æøå"
