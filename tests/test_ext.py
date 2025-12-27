import pytest

from mopidy import config, ext


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


class TestRegistry:
    def test_registry(self):
        reg = ext.Registry()
        assert not len(reg)

        # __iter__ is implemented
        for _entry in reg:
            pass
