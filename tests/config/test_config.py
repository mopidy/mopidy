import unittest
from unittest import mock

from mopidy import config, ext

from tests import path_to_data_dir


class LoadConfigTest(unittest.TestCase):
    def test_load_nothing(self):
        assert {} == config._load([], [], [])

    def test_load_missing_file(self):
        file0 = path_to_data_dir("file0.conf")
        result = config._load([file0], [], [])
        assert {} == result

    @mock.patch("os.access")
    def test_load_nonreadable_file(self, access_mock):
        access_mock.return_value = False
        file1 = path_to_data_dir("file1.conf")
        result = config._load([file1], [], [])
        assert {} == result

    def test_load_single_default(self):
        default = b"[foo]\nbar = baz"
        expected = {"foo": {"bar": "baz"}}
        result = config._load([], [default], [])
        assert expected == result

    def test_unicode_default(self):
        default = "[foo]\nbar = æøå"
        expected = {"foo": {"bar": "æøå"}}
        result = config._load([], [default], [])
        assert expected == result

    def test_load_defaults(self):
        default1 = b"[foo]\nbar = baz"
        default2 = b"[foo2]\n"
        expected = {"foo": {"bar": "baz"}, "foo2": {}}
        result = config._load([], [default1, default2], [])
        assert expected == result

    def test_load_single_override(self):
        override = ("foo", "bar", "baz")
        expected = {"foo": {"bar": "baz"}}
        result = config._load([], [], [override])
        assert expected == result

    def test_load_overrides(self):
        override1 = ("foo", "bar", "baz")
        override2 = ("foo2", "bar", "baz")
        expected = {"foo": {"bar": "baz"}, "foo2": {"bar": "baz"}}
        result = config._load([], [], [override1, override2])
        assert expected == result

    def test_load_single_file(self):
        file1 = path_to_data_dir("file1.conf")
        expected = {"foo": {"bar": "baz"}}
        result = config._load([file1], [], [])
        assert expected == result

    def test_load_files(self):
        file1 = path_to_data_dir("file1.conf")
        file2 = path_to_data_dir("file2.conf")
        expected = {"foo": {"bar": "baz"}, "foo2": {"bar": "baz"}}
        result = config._load([file1, file2], [], [])
        assert expected == result

    def test_load_directory(self):
        directory = path_to_data_dir("conf1.d")
        expected = {"foo": {"bar": "baz"}, "foo2": {"bar": "baz"}}
        result = config._load([directory], [], [])
        assert expected == result

    def test_load_directory_only_conf_files(self):
        directory = path_to_data_dir("conf2.d")
        expected = {"foo": {"bar": "baz"}}
        result = config._load([directory], [], [])
        assert expected == result

    def test_load_file_with_utf8(self):
        expected = {"foo": {"bar": "æøå"}}
        result = config._load([path_to_data_dir("file3.conf")], [], [])
        assert expected == result

    def test_load_file_with_error(self):
        expected = {"foo": {"bar": "baz"}}
        result = config._load([path_to_data_dir("file4.conf")], [], [])
        assert expected == result


class ValidateTest(unittest.TestCase):
    def setUp(self):  # noqa: N802
        self.schema = config.ConfigSchema("foo")
        self.schema["bar"] = config.ConfigValue()

    def test_empty_config_no_schemas(self):
        conf, errors = config._validate({}, [])
        assert {} == conf
        assert {} == errors

    def test_config_no_schemas(self):
        raw_config = {"foo": {"bar": "baz"}}
        conf, errors = config._validate(raw_config, [])
        assert {} == conf
        assert {} == errors

    def test_empty_config_single_schema(self):
        conf, errors = config._validate({}, [self.schema])
        assert {"foo": {"bar": None}} == conf
        assert {"foo": {"bar": "config key not found."}} == errors

    def test_config_single_schema(self):
        raw_config = {"foo": {"bar": "baz"}}
        conf, errors = config._validate(raw_config, [self.schema])
        assert {"foo": {"bar": "baz"}} == conf
        assert {} == errors

    def test_config_single_schema_config_error(self):
        raw_config = {"foo": {"bar": "baz"}}
        self.schema["bar"] = mock.Mock()
        self.schema["bar"].deserialize.side_effect = ValueError("bad")
        conf, errors = config._validate(raw_config, [self.schema])
        assert {"foo": {"bar": None}} == conf
        assert {"foo": {"bar": "bad"}} == errors

    # TODO: add more tests


INPUT_CONFIG = """# comments before first section should work

[section] anything goes ; after the [] block it seems.
; this is a valid comment
this-should-equal-baz = baz ; as this is a comment
this-should-equal-everything = baz # as this is not a comment

# this is also a comment ; and the next line should be a blank comment.
;
# foo # = should all be treated as a comment."""

PROCESSED_CONFIG = """[__COMMENTS__]
__HASH0__ = comments before first section should work
__BLANK1__ =
[section]
__SECTION2__ = anything goes
__INLINE3__ = after the [] block it seems.
__SEMICOLON4__ = this is a valid comment
this-should-equal-baz = baz
__INLINE5__ = as this is a comment
this-should-equal-everything = baz # as this is not a comment
__BLANK6__ =
__HASH7__ = this is also a comment
__INLINE8__ = and the next line should be a blank comment.
__SEMICOLON9__ =
__HASH10__ = foo # = should all be treated as a comment."""


class PreProcessorTest(unittest.TestCase):
    maxDiff = None  # Show entire diff.  # noqa: N815

    def test_empty_config(self):
        result = config._preprocess("")
        assert result == "[__COMMENTS__]"

    def test_plain_section(self):
        result = config._preprocess("[section]\nfoo = bar")
        assert result == "[__COMMENTS__]\n[section]\nfoo = bar"

    def test_initial_comments(self):
        result = config._preprocess("; foobar")
        assert result == "[__COMMENTS__]\n__SEMICOLON0__ = foobar"

        result = config._preprocess("# foobar")
        assert result == "[__COMMENTS__]\n__HASH0__ = foobar"

        result = config._preprocess("; foo\n# bar")
        assert result == "[__COMMENTS__]\n__SEMICOLON0__ = foo\n__HASH1__ = bar"

    def test_initial_comment_inline_handling(self):
        result = config._preprocess("; foo ; bar ; baz")
        assert result == (
            "[__COMMENTS__]\n__SEMICOLON0__ = foo\n"
            "__INLINE1__ = bar\n__INLINE2__ = baz"
        )

    def test_inline_semicolon_comment(self):
        result = config._preprocess("[section]\nfoo = bar ; baz")
        assert (
            result == "[__COMMENTS__]\n[section]\nfoo = bar\n__INLINE0__ = baz"
        )

    def test_no_inline_hash_comment(self):
        result = config._preprocess("[section]\nfoo = bar # baz")
        assert result == "[__COMMENTS__]\n[section]\nfoo = bar # baz"

    def test_section_extra_text(self):
        result = config._preprocess("[section] foobar")
        assert result == "[__COMMENTS__]\n[section]\n__SECTION0__ = foobar"

    def test_section_extra_text_inline_semicolon(self):
        result = config._preprocess("[section] foobar ; baz")
        assert (
            result
            == "[__COMMENTS__]\n[section]\n__SECTION0__ = foobar\n__INLINE1__ = baz"
        )

    def test_conversion(self):
        """Tests all of the above cases at once."""
        result = config._preprocess(INPUT_CONFIG)
        assert result == PROCESSED_CONFIG


class PostProcessorTest(unittest.TestCase):
    maxDiff = None  # Show entire diff.  # noqa: N815

    def test_empty_config(self):
        result = config._postprocess("[__COMMENTS__]")
        assert result == ""

    def test_plain_section(self):
        result = config._postprocess(
            "[__COMMENTS__]\n" "[section]\n" "foo = bar"
        )
        assert result == "[section]\nfoo = bar"

    def test_initial_comments(self):
        result = config._postprocess(
            "[__COMMENTS__]\n" "__SEMICOLON0__ = foobar"
        )
        assert result == "; foobar"

        result = config._postprocess("[__COMMENTS__]\n" "__HASH0__ = foobar")
        assert result == "# foobar"

        result = config._postprocess(
            "[__COMMENTS__]\n" "__SEMICOLON0__ = foo\n" "__HASH1__ = bar"
        )
        assert result == "; foo\n# bar"

    def test_initial_comment_inline_handling(self):
        result = config._postprocess(
            "[__COMMENTS__]\n"
            "__SEMICOLON0__ = foo\n"
            "__INLINE1__ = bar\n"
            "__INLINE2__ = baz"
        )
        assert result == "; foo ; bar ; baz"

    def test_inline_semicolon_comment(self):
        result = config._postprocess(
            "[__COMMENTS__]\n" "[section]\n" "foo = bar\n" "__INLINE0__ = baz"
        )
        assert result == "[section]\nfoo = bar ; baz"

    def test_no_inline_hash_comment(self):
        result = config._preprocess("[section]\nfoo = bar # baz")
        assert result == "[__COMMENTS__]\n[section]\nfoo = bar # baz"

    def test_section_extra_text(self):
        result = config._postprocess(
            "[__COMMENTS__]\n" "[section]\n" "__SECTION0__ = foobar"
        )
        assert result == "[section] foobar"

    def test_section_extra_text_inline_semicolon(self):
        result = config._postprocess(
            "[__COMMENTS__]\n"
            "[section]\n"
            "__SECTION0__ = foobar\n"
            "__INLINE1__ = baz"
        )
        assert result == "[section] foobar ; baz"

    def test_conversion(self):
        result = config._postprocess(PROCESSED_CONFIG)
        assert result == INPUT_CONFIG


def test_format_initial():
    extension = ext.Extension()
    extension.ext_name = "foo"
    extension.get_default_config = lambda: None
    extensions_data = [
        ext.ExtensionData(
            extension=extension,
            entry_point=None,
            config_schema=None,
            config_defaults=None,
            command=None,
        ),
    ]

    result = config.format_initial(extensions_data)

    assert "# For further information" in result
    assert "[foo]\n" in result
