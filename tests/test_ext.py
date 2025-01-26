import pathlib
from importlib import metadata
from unittest import mock

import pytest

from mopidy import config, exceptions, ext
from tests import IsA, any_str


class DummyExtension(ext.Extension):
    dist_name = "Mopidy-Foobar"
    ext_name = "foobar"
    version = "1.2.3"
    location = __file__

    def get_default_config(self):
        return "[foobar]\nenabled = true"


any_testextension = IsA(DummyExtension)


class TestExtension:
    @pytest.fixture
    def extension(self):
        class MyExtension(ext.Extension):
            dist_name = "Mopidy-Foo"
            ext_name = "foo"
            version = "0.1"

        return MyExtension()

    def test_dist_name(self, extension):
        assert extension.dist_name == "Mopidy-Foo"

    def test_ext_name(self, extension):
        assert extension.ext_name == "foo"

    def test_version(self, extension):
        assert extension.version == "0.1"

    def test_get_default_config_raises_not_implemented(self, extension):
        with pytest.raises(NotImplementedError):
            extension.get_default_config()

    def test_get_config_schema_returns_extension_schema(self, extension):
        schema = extension.get_config_schema()
        assert isinstance(schema["enabled"], config.Boolean)

    def test_validate_environment_does_nothing_by_default(self, extension):
        assert extension.validate_environment() is None

    def test_setup_raises_not_implemented(self, extension):
        with pytest.raises(NotImplementedError):
            extension.setup(None)

    def test_get_cache_dir_raises_error(self, extension):
        config = {"core": {"cache_dir": "/tmp"}}
        with pytest.raises(AttributeError):  # ext_name not set
            ext.Extension.get_cache_dir(config)

    def test_get_config_dir_raises_error(self, extension):
        config = {"core": {"config_dir": "/tmp"}}
        with pytest.raises(AttributeError):  # ext_name not set
            ext.Extension.get_config_dir(config)

    def test_get_data_dir_raises_error(self, extension):
        config = {"core": {"data_dir": "/tmp"}}
        with pytest.raises(AttributeError):  # ext_name not set
            ext.Extension.get_data_dir(config)


class TestLoadExtensions:
    @pytest.fixture
    def iter_entry_points_mock(self, request):
        patcher = mock.patch.object(metadata, "entry_points")
        iter_entry_points = patcher.start()
        iter_entry_points.return_value = []
        yield iter_entry_points
        patcher.stop()

    @pytest.fixture
    def mock_entry_point(self, iter_entry_points_mock):
        entry_point = mock.Mock()
        entry_point.load = mock.Mock(return_value=DummyExtension)
        iter_entry_points_mock.return_value = [entry_point]
        return entry_point

    def test_no_extensions(self, iter_entry_points_mock):
        assert ext.load_extensions() == []

    def test_load_extensions(self, mock_entry_point):
        expected = ext.ExtensionData(
            any_testextension,
            mock_entry_point,
            IsA(config.ConfigSchema),
            any_str,
            None,
        )
        assert ext.load_extensions() == [expected]

    def test_load_extensions_exception(self, mock_entry_point, caplog):
        mock_entry_point.load.side_effect = Exception("test")
        ext.load_extensions()
        assert "Failed to load extension" in caplog.records[0].message

    def test_load_extensions_real(self):
        installed_extensions = ext.load_extensions()
        assert len(installed_extensions)

    def test_gets_wrong_class(self, mock_entry_point):
        class WrongClass:
            pass

        mock_entry_point.load.return_value = WrongClass
        assert ext.load_extensions() == []

    def test_gets_instance(self, mock_entry_point):
        mock_entry_point.load.return_value = DummyExtension()
        assert ext.load_extensions() == []

    def test_creating_instance_fails(self, mock_entry_point):
        mock_entry_point.load.return_value = mock.Mock(side_effect=Exception)
        assert ext.load_extensions() == []

    def test_get_config_schema_fails(self, mock_entry_point):
        with mock.patch.object(DummyExtension, "get_config_schema") as get:
            get.side_effect = Exception

            assert ext.load_extensions() == []
            get.assert_called_once_with()

    def test_get_default_config_fails(self, mock_entry_point):
        with mock.patch.object(DummyExtension, "get_default_config") as get:
            get.side_effect = Exception

            assert ext.load_extensions() == []
            get.assert_called_once_with()

    def test_get_command_fails(self, mock_entry_point):
        with mock.patch.object(DummyExtension, "get_command") as get:
            get.side_effect = Exception

            assert ext.load_extensions() == []
            get.assert_called_once_with()


class TestValidateExtensionData:
    @pytest.fixture
    def ext_data(self):
        extension = DummyExtension()
        entry_point = mock.Mock()
        entry_point.name = extension.ext_name
        return ext.ExtensionData(
            extension,
            entry_point,
            extension.get_config_schema(),
            extension.get_default_config(),
            extension.get_command(),
        )

    def test_real(self):
        for dist in ext.load_extensions():
            assert ext.validate_extension_data(dist)

    def test_ok(self, ext_data):
        assert ext.validate_extension_data(ext_data)

    def test_name_mismatch(self, ext_data):
        ext_data.entry_point.name = "barfoo"
        assert not ext.validate_extension_data(ext_data)

    def test_distribution_not_found(self, ext_data):
        error = metadata.PackageNotFoundError
        ext_data.entry_point.load.side_effect = error
        assert not ext.validate_extension_data(ext_data)

    def test_entry_point_require_exception(self, ext_data):
        ext_data.entry_point.load.side_effect = Exception("Some extension error")

        # Hope that entry points are well behaved, so exception will bubble.
        with pytest.raises(Exception, match="Some extension error"):
            assert not ext.validate_extension_data(ext_data)

    def test_extenions_validate_environment_error(self, ext_data):
        extension = ext_data.extension
        with mock.patch.object(extension, "validate_environment") as validate:
            validate.side_effect = exceptions.ExtensionError("error")

            assert not ext.validate_extension_data(ext_data)
            validate.assert_called_once_with()

    def test_extenions_validate_environment_exception(self, ext_data):
        extension = ext_data.extension
        with mock.patch.object(extension, "validate_environment") as validate:
            validate.side_effect = Exception

            assert not ext.validate_extension_data(ext_data)
            validate.assert_called_once_with()

    def test_missing_schema(self, ext_data):
        ext_data = ext_data._replace(config_schema=None)
        assert not ext.validate_extension_data(ext_data)

    def test_schema_that_is_missing_enabled(self, ext_data):
        del ext_data.config_schema["enabled"]
        ext_data.config_schema["baz"] = config.String()
        assert not ext.validate_extension_data(ext_data)

    def test_schema_with_wrong_types(self, ext_data):
        ext_data.config_schema["enabled"] = 123
        assert not ext.validate_extension_data(ext_data)

    def test_schema_with_invalid_type(self, ext_data):
        ext_data.config_schema["baz"] = 123
        assert not ext.validate_extension_data(ext_data)

    def test_no_default_config(self, ext_data):
        ext_data = ext_data._replace(config_defaults=None)
        assert not ext.validate_extension_data(ext_data)

    def test_get_cache_dir(self, ext_data):
        core_cache_dir = "/tmp"
        config = {"core": {"cache_dir": core_cache_dir}}
        extension = ext_data.extension

        with mock.patch.object(ext.path, "get_or_create_dir"):
            cache_dir = extension.get_cache_dir(config)

        expected = pathlib.Path(core_cache_dir).resolve() / extension.ext_name
        assert cache_dir == expected

    def test_get_config_dir(self, ext_data):
        core_config_dir = "/tmp"
        config = {"core": {"config_dir": core_config_dir}}
        extension = ext_data.extension

        with mock.patch.object(ext.path, "get_or_create_dir"):
            config_dir = extension.get_config_dir(config)

        expected = pathlib.Path(core_config_dir).resolve() / extension.ext_name
        assert config_dir == expected

    def test_get_data_dir(self, ext_data):
        core_data_dir = "/tmp"
        config = {"core": {"data_dir": core_data_dir}}
        extension = ext_data.extension

        with mock.patch.object(ext.path, "get_or_create_dir"):
            data_dir = extension.get_data_dir(config)

        expected = pathlib.Path(core_data_dir).resolve() / extension.ext_name
        assert data_dir == expected


class TestRegistry:
    def test_registry(self):
        reg = ext.Registry()
        assert not len(reg)

        # __iter__ is implemented
        for _entry in reg:
            pass
