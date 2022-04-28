import codecs
import logging
import re
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
        assert not isinstance(result, types._TransformedValue)

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

    @pytest.mark.parametrize(
        ("original", "transformed"),
        (
            ("abc", "abc"),
            ("ABC", "abc"),
            ("aBc", "abc"),
            ("123", "123"),
            ("abc123def456", "abc123def456"),
            ("ABC123def456GHI789", "abc123def456ghi789"),
        ),
    )
    def test_deserialize_utilises_transformer(
        self, original: str, transformed: str
    ):
        cv = types.String(transformer=lambda value: value.lower())

        result = cv.deserialize(original)
        assert isinstance(result, str)
        assert isinstance(result, types._TransformedValue)
        assert result == transformed
        assert result.original == original

    @pytest.mark.parametrize(
        ("original", "transformed"),
        (
            ("abc", "abc"),
            ("ABC", "abc"),
            ("aBc", "abc"),
            ("123", "123"),
            ("abc123def456", "abc123def456"),
            ("ABC123def456GHI789", "abc123def456ghi789"),
        ),
    )
    def test_serialize_transformed_value(self, original: str, transformed: str):
        cv = types.String()
        transformed_value = types._TransformedValue(original, transformed)

        result = cv.serialize(transformed_value)
        assert isinstance(result, str)
        assert not isinstance(result, types._TransformedValue)
        assert result == original


class TestSecret:
    def test_deserialize_decodes_utf8(self):
        cv = types.Secret()

        result = cv.deserialize("æøå".encode())

        assert isinstance(result, str)
        assert not isinstance(result, types._TransformedValue)
        assert result == "æøå"

    def test_deserialize_enforces_required(self):
        cv = types.Secret()

        with pytest.raises(ValueError):
            cv.deserialize(b"")

    def test_deserialize_respects_optional(self):
        cv = types.Secret(optional=True)

        assert cv.deserialize(b"") is None
        assert cv.deserialize(b" ") is None

    def test_deserialize_utilises_transformer(self):
        cv = types.Secret(
            transformer=lambda value: codecs.decode(value, encoding="rot13")
        )

        result = cv.deserialize("zbcvql")

        assert isinstance(result, str)
        assert isinstance(result, types._TransformedValue)
        assert result == "mopidy"
        assert result.original == "zbcvql"

    def test_serialize_none(self):
        cv = types.Secret()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == ""

    def test_serialize_transformed_value(self):
        cv = types.Secret()
        transformed_value = types._TransformedValue("zbcvql", "mopidy")

        result = cv.serialize(transformed_value)

        assert isinstance(result, str)
        assert not isinstance(result, types._TransformedValue)
        assert result == "zbcvql"

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

    def test_serialize_transformed_value_for_display_masks_value(self):
        cv = types.Secret()
        transformed_value = types._TransformedValue("zbcvql", "mopidy")

        result = cv.serialize(transformed_value, display=True)

        assert isinstance(result, str)
        assert not isinstance(result, types._TransformedValue)
        assert result == "********"


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

        assert cv.deserialize("3") == 3

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


class TestFloat:
    def test_deserialize_conversion_success(self):
        cv = types.Float()

        assert cv.deserialize("123") == 123.0
        assert cv.deserialize("0") == 0.0
        assert cv.deserialize("-10") == -10.0
        assert cv.deserialize("3.14") == 3.14
        assert cv.deserialize("123.45") == 123.45
        assert cv.deserialize("-456.78") == -456.78

    def test_deserialize_conversion_failure(self):
        cv = types.Float()

        errmsg = re.escape("could not convert string to float")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("asd")

    def test_deserialize_enforces_required(self):
        cv = types.Float()

        errmsg = "must be set"
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("")

    def test_deserialize_respects_optional(self):
        cv = types.Float(optional=True)

        assert cv.deserialize("") is None

    def test_deserialize_enforces_minimum(self):
        cv = types.Float(minimum=10)

        assert cv.deserialize("10.1") == 10.1

        errmsg = re.escape("must be larger than")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("9.9")

    def test_deserialize_enforces_maximum(self):
        cv = types.Float(maximum=10)

        assert cv.deserialize("9.9") == 9.9

        errmsg = re.escape("must be smaller than")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("10.1")


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


class TestPair:
    def test_deserialize_conversion_success(self):
        cv = types.Pair()

        result = cv.deserialize("foo|bar")
        assert result == ("foo", "bar")

        result = cv.deserialize("  foo|bar")
        assert result == ("foo", "bar")

        result = cv.deserialize("foo|bar  ")
        assert result == ("foo", "bar")

        result = cv.deserialize("  fo o | bar ")
        assert result == ("fo o", "bar")

        result = cv.deserialize("foo|bar|baz")
        assert result == ("foo", "bar|baz")

    def test_deserialize_decodes_utf8(self):
        cv = types.Pair()

        result = cv.deserialize("æ|å".encode())
        assert result == ("æ", "å")

        result = cv.deserialize("æ | ø\n".encode())
        assert result == ("æ", "ø")

        result = cv.deserialize("æ ø| å".encode())
        assert result == ("æ ø", "å")

        result = cv.deserialize(" æ | øå \n".encode())
        assert result == ("æ", "øå")

    def test_deserialize_enforces_required(self):
        cv = types.Pair()

        errmsg = re.escape("must be set")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("")

    def test_deserialize_respects_optional(self):
        cv = types.Pair(optional=True)

        assert cv.deserialize("") is None
        assert cv.deserialize(" ") is None

    def test_deserialize_enforces_required_separator(self):
        cv = types.Pair()

        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: abc")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc")

    def test_deserialize_respects_optional_separator(self):
        cv = types.Pair(optional_pair=True)

        result = cv.deserialize("abc")
        assert result == ("abc", "abc")

        result = cv.deserialize("abc|def")
        assert result == ("abc", "def")

    @pytest.mark.parametrize(
        "sep", ("!", "@", "#", "$", "%", "^", "&", "*", "/", "\\")
    )
    def test_deserialize_respects_custom_separator(self, sep: str):
        cv = types.Pair(separator=sep)

        result = cv.deserialize(f"abc{sep}def")
        assert result == ("abc", "def")

        result = cv.deserialize(f"abc|def{sep}ghi|jkl")
        assert result == ("abc|def", "ghi|jkl")

        result = cv.deserialize(f"abc{sep}def{sep}ghi")
        assert result == ("abc", f"def{sep}ghi")

        result = cv.deserialize(f"ab|cd{sep}ef|gh{sep}ij|kl")
        assert result == ("ab|cd", f"ef|gh{sep}ij|kl")

        result = cv.deserialize(f"|abcd|{sep}efgh|")
        assert result == ("|abcd|", "efgh|")

        errmsg = (
            "^"
            + re.escape(f"Config value must include {sep!r} separator: abc|def")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def")

    @pytest.mark.parametrize(
        "sep", ("!", "@", "#", "$", "%", "^", "&", "*", "/", "\\")
    )
    def test_deserialize_respects_optional_custom_separator(self, sep: str):
        cv = types.Pair(optional_pair=True, separator=sep)

        result = cv.deserialize(f"abc{sep}def")
        assert result == ("abc", "def")

        result = cv.deserialize("abcdef")
        assert result == ("abcdef", "abcdef")

        result = cv.deserialize("abc|def")
        assert result == ("abc|def", "abc|def")

        result = cv.deserialize(f"|abc{sep}def|")
        assert result == ("|abc", "def|")

    @pytest.mark.parametrize("optional", (True, False))
    @pytest.mark.parametrize("optional_pair", (True, False))
    def test_deserialize_enforces_required_pair_values(
        self, optional: bool, optional_pair: bool
    ):
        cv = types.Pair(optional=optional, optional_pair=optional_pair)

        errmsg = re.escape("must be set")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("|def")

    @pytest.mark.parametrize("optional", (True, False))
    @pytest.mark.parametrize("optional_pair", (True, False))
    @pytest.mark.parametrize(
        "sep", ("!", "@", "#", "$", "%", "^", "&", "*", "/", "\\")
    )
    def test_deserialize_enforces_required_pair_values_with_custom_separator(
        self, optional: bool, optional_pair: bool, sep: str
    ):
        cv = types.Pair(
            optional=optional, optional_pair=optional_pair, separator=sep
        )

        errmsg = re.escape("must be set")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize(f"abc{sep}")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize(f"{sep}def")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize(f"abc|def{sep}")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize(f"{sep}ghi|jkl")

    def test_deserialize_with_custom_subtypes(self):
        cv = types.Pair(subtypes=(types.String(), types.Integer()))
        result = cv.deserialize("abc|10")
        assert result == ("abc", 10)

        cv = types.Pair(subtypes=(types.Float(), types.Boolean()))
        result = cv.deserialize("3.14|true")
        assert result == (3.14, True)

        cv = types.Pair(subtypes=(types.Path(), types.String()))
        result = cv.deserialize("/dev/null | empty")
        assert result == ("/dev/null", "empty")

        with mock.patch("socket.getaddrinfo") as getaddrinfo_mock:
            cv = types.Pair(subtypes=(types.Hostname(), types.Port()))
            result = cv.deserialize("localhost|6680")
            assert result == ("localhost", 6680)
            getaddrinfo_mock.assert_called_once_with("localhost", None)

    def test_deserialize_with_custom_subtypes_enforces_required(self):
        cv = types.Pair(subtypes=(types.Integer(), types.Integer()))

        errmsg = re.escape("must be set")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("")

    def test_deserialize_with_custom_subtypes_respects_optional(self):
        cv = types.Pair(optional=True, subtypes=(types.Float(), types.Float()))

        assert cv.deserialize("") is None

    def test_deserialize_with_custom_subtypes_enforces_required_separator(self):
        errmsg = "^" + re.escape("Config value must include '|' separator: ")

        cv = types.Pair(subtypes=(types.String(), types.Secret()))
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc")

        cv = types.Pair(subtypes=(types.String(), types.Integer()))
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("123")

    def test_deserialize_with_custom_subtypes_respects_optional_separator(self):
        cv = types.Pair(
            optional_pair=True, subtypes=(types.Integer(), types.Integer())
        )
        result = cv.deserialize("42")
        assert result == (42, 42)

        cv = types.Pair(
            optional_pair=True, subtypes=(types.Path(), types.String())
        )
        result = cv.deserialize("/dev/null")
        assert result == ("/dev/null", "/dev/null")

        cv = types.Pair(
            optional_pair=True, subtypes=(types.Port(), types.Port())
        )
        result = cv.deserialize("443")
        assert result == (443, 443)

    def test_deserialize_with_custom_subtypes_optional_separator_mixed_types(
        self,
    ):
        cv = types.Pair(
            optional_pair=True, subtypes=(types.String(), types.Integer())
        )

        errmsg = re.escape("invalid literal for int() with base 10")

        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc")

    def test_deserialize_with_optional_custom_subtypes(self):
        cv = types.Pair(subtypes=(types.String(), types.String(optional=True)))
        result = cv.deserialize("abc|")
        assert result == ("abc", None)

        cv = types.Pair(subtypes=(types.String(optional=True), types.String()))
        result = cv.deserialize("|def")
        assert result == (None, "def")

        cv = types.Pair(
            subtypes=(types.String(optional=True), types.String(optional=True))
        )
        result = cv.deserialize("|")
        assert result == (None, None)

    def test_serialize(self):
        cv = types.Pair()
        result = cv.serialize(("abc", "def"))
        assert result == "abc|def"
        result = cv.serialize(("abc", None))
        assert result == "abc|"
        result = cv.serialize((None, "abc"))
        assert result == "|abc"

        cv = types.Pair(subtypes=(types.String(), types.Integer()))
        result = cv.serialize(("abc", 42))
        assert result == "abc|42"
        result = cv.serialize(("abc", None))
        assert result == "abc|"
        result = cv.serialize((None, 42))
        assert result == "|42"

        cv = types.Pair(subtypes=(types.String(), types.Path()))
        result = cv.serialize(("null", "/dev/null"))
        assert result == "null|/dev/null"
        result = cv.serialize(("tmp", types._ExpandedPath("/tmp", "/tmp")))
        assert result == "tmp|/tmp"
        result = cv.serialize(("null", None))
        assert result == "null|"
        result = cv.serialize(
            (None, types._ExpandedPath("/dev/null", "/dev/null"))
        )
        assert result == "|/dev/null"

    @pytest.mark.parametrize(
        "sep", ("!", "@", "#", "$", "%", "^", "&", "*", "/", "\\")
    )
    def test_serialize_with_custom_separator(self, sep: str):
        cv = types.Pair(separator=sep)
        result = cv.serialize(("abc", "def"))
        assert result == f"abc{sep}def"
        result = cv.serialize(("abc", None))
        assert result == f"abc{sep}"
        result = cv.serialize((None, "abc"))
        assert result == f"{sep}abc"

        cv = types.Pair(
            separator=sep, subtypes=(types.String(), types.Integer())
        )
        result = cv.serialize(("abc", 42))
        assert result == f"abc{sep}42"
        result = cv.serialize(("abc", None))
        assert result == f"abc{sep}"
        result = cv.serialize((None, 42))
        assert result == f"{sep}42"

        cv = types.Pair(separator=sep, subtypes=(types.String(), types.Path()))
        result = cv.serialize(("null", "/dev/null"))
        assert result == f"null{sep}/dev/null"
        result = cv.serialize(("tmp", types._ExpandedPath("/tmp", "/tmp")))
        assert result == f"tmp{sep}/tmp"
        result = cv.serialize(("null", None))
        assert result == f"null{sep}"
        result = cv.serialize(
            (None, types._ExpandedPath("/dev/null", "/dev/null"))
        )
        assert result == f"{sep}/dev/null"

    def test_serialize_returns_single_value_with_optional_pair(self):
        cv = types.Pair(optional_pair=True)

        result = cv.serialize(("abc", "abc"))
        assert result == "abc"

        result = cv.serialize(("abc", "def"))
        assert result == "abc|def"

        result = cv.serialize(("abc", "abc"), display=True)
        assert result == "abc|abc"

        result = cv.serialize(("abc", "def"), display=True)
        assert result == "abc|def"

    def test_deserialize_nested_pair_success(self):
        cv = types.Pair(subtypes=(types.Integer(), types.Pair()))
        result = cv.deserialize("50|def|ghi")
        assert result == (50, ("def", "ghi"))

        cv = types.Pair(
            separator="#",
            subtypes=(
                types.String(),
                types.Pair(subtypes=(types.Integer(), types.Integer())),
            ),
        )
        result = cv.deserialize("xyz#4|-5")
        assert result == ("xyz", (4, -5))

        cv = types.Pair(
            subtypes=(
                types.Pair(
                    separator="*", subtypes=(types.Float(), types.Float())
                ),
                types.String(),
            ),
        )
        result = cv.deserialize("42*2.5|abc")
        assert result == ((42, 2.5), "abc")

        cv = types.Pair(
            subtypes=(
                types.Pair(separator="#"),
                types.Pair(),
            ),
        )
        result = cv.deserialize("abc#def|ghi|jkl")
        assert result == (("abc", "def"), ("ghi", "jkl"))

    def test_deserialize_nested_pair_fail(self):
        cv = types.Pair(
            subtypes=(
                types.Pair(),
                types.String(),
            ),
        )
        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: abc")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def|ghi")

        cv = types.Pair(
            optional_pair=True,
            subtypes=(
                types.Pair(),
                types.String(),
            ),
        )
        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: abc")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def|ghi")

        cv = types.Pair(
            optional_pair=True,
            subtypes=(
                types.String(),
                types.Pair(),
            ),
        )
        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: def")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def")

        cv = types.Pair(
            subtypes=(
                types.Pair(),
                types.Pair(separator="#"),
            ),
        )
        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: abc")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def|ghi#jkl")

    def test_deserialize_nested_pair_optional(self):
        cv = types.Pair(
            subtypes=(
                types.Pair(optional=True),
                types.Pair(),
            )
        )
        result = cv.deserialize("|abc|def")
        assert result == (None, ("abc", "def"))

        cv = types.Pair(
            subtypes=(
                types.Pair(),
                types.Pair(optional=True),
            ),
        )
        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: abc")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def|")

        cv = types.Pair(
            subtypes=(
                types.Pair(separator="#"),
                types.Pair(optional=True),
            ),
        )
        result = cv.deserialize("abc#def|")
        assert result == (("abc", "def"), None)

        cv = types.Pair(
            separator="#",
            subtypes=(
                types.Pair(),
                types.Pair(optional=True),
            ),
        )
        result = cv.deserialize("mno|xyz#")
        assert result == (("mno", "xyz"), None)

        cv = types.Pair(
            subtypes=(
                types.Pair(optional=True),
                types.Pair(optional=True),
            ),
        )
        result = cv.deserialize("|")
        assert result == (None, None)

    def test_deserialize_nested_pair_optional_pair(self):
        cv = types.Pair(
            subtypes=(
                types.Pair(optional_pair=True),
                types.String(),
            ),
        )
        result = cv.deserialize("abc|def|ghi")
        assert result == (("abc", "abc"), "def|ghi")

        cv = types.Pair(
            subtypes=(
                types.String(),
                types.Pair(optional_pair=True),
            )
        )
        result = cv.deserialize("abc|def")
        assert result == ("abc", ("def", "def"))

        cv = types.Pair(
            subtypes=(
                types.Pair(optional_pair=True),
                types.Pair(),
            ),
        )
        result = cv.deserialize("abc|def|ghi")
        assert result == (("abc", "abc"), ("def", "ghi"))

        cv = types.Pair(
            subtypes=(
                types.Pair(),
                types.Pair(optional_pair=True),
            ),
        )
        errmsg = (
            "^"
            + re.escape("Config value must include '|' separator: abc")
            + "$"
        )
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("abc|def|ghi")

        cv = types.Pair(
            subtypes=(
                types.Pair(separator="#"),
                types.Pair(optional_pair=True),
            ),
        )
        result = cv.deserialize("abc#def|ghi")
        assert result == (("abc", "def"), ("ghi", "ghi"))

        cv = types.Pair(
            subtypes=(
                types.Pair(optional_pair=True),
                types.Pair(optional_pair=True),
            ),
        )
        result = cv.deserialize("abc|def")
        assert result == (("abc", "abc"), ("def", "def"))

        errmsg = re.escape("must be set")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("|")

        cv = types.Pair(
            optional_pair=True,
            subtypes=(
                types.Pair(optional_pair=True),
                types.Pair(optional_pair=True),
            ),
        )
        result = cv.deserialize("abc")
        assert result == (("abc", "abc"), ("abc", "abc"))

    def test_serialize_nested_pair(self):
        cv = types.Pair(subtypes=(types.String(), types.Pair()))
        result = cv.serialize(("abc", ("def", "ghi")))
        assert result == "abc|def|ghi"

        cv = types.Pair(
            subtypes=(
                types.Pair(separator="#"),
                types.String(),
            ),
        )
        result = cv.serialize((("abc", "def"), "ghi"))
        assert result == "abc#def|ghi"

        cv = types.Pair(
            separator="#",
            subtypes=(types.Pair(), types.Pair()),
        )
        result = cv.serialize((("abc", "def"), ("ghi", "jkl")))
        assert result == "abc|def#ghi|jkl"

        cv = types.Pair(
            optional_pair=True,
            subtypes=(
                types.Pair(optional_pair=True),
                types.Pair(optional_pair=True),
            ),
        )
        result = cv.serialize((("abc", "abc"), ("abc", "abc")))
        assert result == "abc"
        result = cv.serialize((("abc", "abc"), ("abc", "abc")), display=True)
        assert result == "abc|abc|abc|abc"


class TestList:
    # TODO: add test_deserialize_handles_escapes

    def test_deserialize_conversion_success(self):
        cv = types.List()

        result = cv.deserialize(b"foo, bar ,baz ")
        assert result == ("foo", "bar", "baz")

        result = cv.deserialize(b" foo,bar\nbar\nbaz")
        assert result == ("foo,bar", "bar", "baz")

    def test_deserialize_conversion_success_unique(self):
        cv = types.List(unique=True)

        result = cv.deserialize("foo, bar, baz ")
        assert result == {"foo", "bar", "baz"}

        result = cv.deserialize("foo,bar,foo,baz,foo")
        assert result == {"foo", "bar", "baz"}

        result = cv.deserialize(" foo,bar\nbar\nbaz")
        assert result == {"foo,bar", "bar", "baz"}

    def test_deserialize_creates_tuples(self):
        cv = types.List(optional=True)

        assert isinstance(cv.deserialize(b"foo,bar,baz"), tuple)
        assert isinstance(cv.deserialize(b""), tuple)

    def test_deserialize_creates_frozensets(self):
        cv = types.List(optional=True, unique=True)

        assert isinstance(cv.deserialize("foo,bar,baz"), frozenset)
        assert isinstance(cv.deserialize(""), frozenset)

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

    @pytest.mark.parametrize(
        "value",
        (
            "foo,,bar,,baz",
            "foo, ,bar, , baz",
            "foo, ,bar, , baz, ",
            "foo\n\nbar\n\nbaz\n",
            "foo \n bar \n \n baz",
        ),
    )
    def test_deserialize_ignores_blanks(self, value):
        cv = types.List()

        result = cv.deserialize(value)
        assert result == ("foo", "bar", "baz")

    def test_serialize_tuples(self):
        cv = types.List()

        result = cv.serialize(("foo", "bar", "baz"))

        assert isinstance(result, str)
        assert result == "\n  foo\n  bar\n  baz"

    def test_serialize_sets(self):
        cv = types.List(unique=True)

        result = cv.serialize({"foo", "bar", "baz"})

        assert isinstance(result, str)
        assert "\n  foo" in result
        assert "\n  bar" in result
        assert "\n  baz" in result

    def test_serialize_none(self):
        cv = types.List()

        result = cv.serialize(None)

        assert isinstance(result, str)
        assert result == ""

    @pytest.mark.parametrize(
        "value",
        (
            ("foo", "", "bar", "baz"),
            ("foo", "bar", "", "", "baz"),
        ),
    )
    def test_serialize_ignores_blanks(self, value):
        cv = types.List()

        result = cv.serialize(value)

        assert result == "\n  foo\n  bar\n  baz"

    def test_serialize_ignores_blanks_sets(self):
        cv = types.List(unique=True)

        result = cv.serialize({"foo", "", "bar", "baz"})
        assert "\n  foo" in result
        assert "\n  bar" in result
        assert "\n  baz" in result
        assert "\n  \n" not in result
        assert not result.endswith("\n  ")

    def test_deserialize_with_custom_subtype(self):
        cv = types.List(subtype=types.Integer())
        expected = (1, 2, 3)
        assert cv.deserialize("1, 2, 3") == expected
        assert cv.deserialize("1\n2\n3") == expected
        assert cv.deserialize("\n  1\n  2\n  3") == expected

        cv = types.List(subtype=types.Pair())
        expected = (("a", "x"), ("b", "y"), ("c", "z"))
        assert cv.deserialize("a|x,b|y,c|z") == expected
        assert cv.deserialize("a|x\nb|y\nc|z") == expected
        assert cv.deserialize("\n  a|x\n  b|y\n  c|z") == expected

        cv = types.List(
            subtype=types.Pair(subtypes=(types.Integer(), types.Integer())),
        )
        expected = ((7, 1), (8, 2), (9, 3))
        assert cv.deserialize("7|1,8|2,9|3") == expected
        assert cv.deserialize("7|1\n8|2\n9|3") == expected
        assert cv.deserialize("\n  7|1\n  8|2\n  9|3") == expected

        with mock.patch("socket.getaddrinfo") as getaddrinfo_mock:
            cv = types.List(
                subtype=types.Pair(subtypes=(types.Hostname(), types.Port())),
            )
            expected = (("localhost", 8080), ("example.com", 443))
            assert cv.deserialize("localhost|8080,example.com|443") == expected
            assert cv.deserialize("localhost|8080\nexample.com|443") == expected
            call_localhost = mock.call("localhost", None)
            call_examplecom = mock.call("example.com", None)
            assert getaddrinfo_mock.mock_calls == [
                call_localhost,
                call_examplecom,
                call_localhost,
                call_examplecom,
            ]

    def test_deserialize_with_custom_subtype_enforces_required(self):
        cv = types.List(subtype=types.Float())

        errmsg = re.escape("must be set")
        with pytest.raises(ValueError, match=errmsg):
            cv.deserialize("")

    def test_deserialize_with_custom_subtype_respects_optional(self):
        cv = types.List(optional=True, subtype=types.Float())

        assert cv.deserialize("") == ()

    def test_serialize_with_custom_subtype(self):
        cv = types.List(subtype=types.Integer())
        result = cv.serialize((1, 2, 3))
        assert result == "\n  1\n  2\n  3"

        cv = types.List(subtype=types.Pair())
        result = cv.serialize((("a", "x"), ("b", "y"), ("c", "z")))
        assert result == "\n  a|x\n  b|y\n  c|z"

        cv = types.List(
            subtype=types.Pair(
                separator="#",
                subtypes=(types.Integer(), types.Integer()),
            ),
        )
        result = cv.serialize(((7, 1), (8, 2), (9, 3)))
        assert result == "\n  7#1\n  8#2\n  9#3"


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
            assert cv.serialize(level) == name

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

    def test_serialize_none(self):
        cv = types.Path()

        assert cv.serialize(None) == ""
