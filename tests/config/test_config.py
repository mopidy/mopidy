import unittest
from unittest import mock

from mopidy import config, ext
from tests import path_to_data_dir


class LoadConfigTest(unittest.TestCase):
    def test_load_nothing(self):
        assert config._load([], [], []) == {}

    def test_load_missing_file(self):
        file0 = path_to_data_dir("file0.conf")
        result = config._load([file0], [], [])
        assert result == {}

    @mock.patch("os.access")
    def test_load_nonreadable_file(self, access_mock):
        access_mock.return_value = False
        file1 = path_to_data_dir("file1.conf")
        result = config._load([file1], [], [])
        assert result == {}

    def test_load_single_default(self):
        default = b"[foo]\nbar = baz"
        expected = {"foo": {"bar": "baz"}}
        result = config._load([], [default], [])
        assert expected == result

    def test_load_ignore_inline_comment(self):
        default = b"[foo]\nbar = baz ; my_comment"
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
    def setUp(self):
        self.schema = config.ConfigSchema("foo")
        self.schema["bar"] = config.String()

    def test_empty_config_no_schemas(self):
        conf, errors = config._validate({}, [])
        assert conf == {}
        assert errors == {}

    def test_config_no_schemas(self):
        raw_config = {"foo": {"bar": "baz"}}
        conf, errors = config._validate(raw_config, [])
        assert conf == {}
        assert errors == {}

    def test_empty_config_single_schema(self):
        conf, errors = config._validate({}, [self.schema])
        assert conf == {"foo": {"bar": None}}
        assert errors == {"foo": {"bar": "config key not found."}}

    def test_config_single_schema(self):
        raw_config = {"foo": {"bar": "baz"}}
        conf, errors = config._validate(raw_config, [self.schema])
        assert conf == {"foo": {"bar": "baz"}}
        assert errors == {}

    def test_config_single_schema_config_error(self):
        raw_config = {"foo": {"bar": "baz"}}
        self.schema["bar"] = mock.Mock()
        self.schema["bar"].deserialize.side_effect = ValueError("bad")
        conf, errors = config._validate(raw_config, [self.schema])
        assert conf == {"foo": {"bar": None}}
        assert errors == {"foo": {"bar": "bad"}}

    # TODO: add more tests


def test_format_initial():
    extension = ext.Extension()
    extension.dist_name = "Mopidy-Foo"
    extension.ext_name = "foo"
    extension.version = "0.1"
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
