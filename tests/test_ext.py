from __future__ import absolute_import, unicode_literals

import os

import mock

import pkg_resources

import pytest

from mopidy import config, exceptions, ext

from tests import IsA, any_unicode


class DummyExtension(ext.Extension):
    dist_name = 'Mopidy-Foobar'
    ext_name = 'foobar'
    version = '1.2.3'

    def get_default_config(self):
        return '[foobar]\nenabled = true'


any_testextension = IsA(DummyExtension)


class TestExtension(object):

    @pytest.fixture
    def extension(self):
        return ext.Extension()

    def test_dist_name_is_none(self, extension):
        assert extension.dist_name is None

    def test_ext_name_is_none(self, extension):
        assert extension.ext_name is None

    def test_version_is_none(self, extension):
        assert extension.version is None

    def test_get_default_config_raises_not_implemented(self, extension):
        with pytest.raises(NotImplementedError):
            extension.get_default_config()

    def test_get_config_schema_returns_extension_schema(self, extension):
        schema = extension.get_config_schema()
        assert isinstance(schema['enabled'], config.Boolean)

    def test_validate_environment_does_nothing_by_default(self, extension):
        assert extension.validate_environment() is None

    def test_setup_raises_not_implemented(self, extension):
        with pytest.raises(NotImplementedError):
            extension.setup(None)

    def test_get_cache_dir_raises_assertion_error(self, extension):
        config = {'core': {'cache_dir': '/tmp'}}
        with pytest.raises(AssertionError):  # ext_name not set
            ext.Extension.get_cache_dir(config)

    def test_get_config_dir_raises_assertion_error(self, extension):
        config = {'core': {'config_dir': '/tmp'}}
        with pytest.raises(AssertionError):  # ext_name not set
            ext.Extension.get_config_dir(config)

    def test_get_data_dir_raises_assertion_error(self, extension):
        config = {'core': {'data_dir': '/tmp'}}
        with pytest.raises(AssertionError):  # ext_name not set
            ext.Extension.get_data_dir(config)


class TestLoadExtensions(object):

    @pytest.yield_fixture
    def iter_entry_points_mock(self, request):
        patcher = mock.patch('pkg_resources.iter_entry_points')
        iter_entry_points = patcher.start()
        iter_entry_points.return_value = []
        yield iter_entry_points
        patcher.stop()

    def test_no_extensions(self, iter_entry_points_mock):
        iter_entry_points_mock.return_value = []
        assert ext.load_extensions() == []

    def test_load_extensions(self, iter_entry_points_mock):
        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = DummyExtension

        iter_entry_points_mock.return_value = [mock_entry_point]

        expected = ext.ExtensionData(
            any_testextension, mock_entry_point, IsA(config.ConfigSchema),
            any_unicode, None)

        assert ext.load_extensions() == [expected]

    def test_gets_wrong_class(self, iter_entry_points_mock):

        class WrongClass(object):
            pass

        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = WrongClass

        iter_entry_points_mock.return_value = [mock_entry_point]

        assert ext.load_extensions() == []

    def test_gets_instance(self, iter_entry_points_mock):
        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = DummyExtension()

        iter_entry_points_mock.return_value = [mock_entry_point]

        assert ext.load_extensions() == []

    def test_creating_instance_fails(self, iter_entry_points_mock):
        mock_extension = mock.Mock(spec=ext.Extension)
        mock_extension.side_effect = Exception

        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = mock_extension

        iter_entry_points_mock.return_value = [mock_entry_point]

        assert ext.load_extensions() == []

    def test_get_config_schema_fails(self, iter_entry_points_mock):
        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = DummyExtension

        iter_entry_points_mock.return_value = [mock_entry_point]

        with mock.patch.object(DummyExtension, 'get_config_schema') as get:
            get.side_effect = Exception

            assert ext.load_extensions() == []
            get.assert_called_once_with()

    def test_get_default_config_fails(self, iter_entry_points_mock):
        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = DummyExtension

        iter_entry_points_mock.return_value = [mock_entry_point]

        with mock.patch.object(DummyExtension, 'get_default_config') as get:
            get.side_effect = Exception

            assert ext.load_extensions() == []
            get.assert_called_once_with()

    def test_get_command_fails(self, iter_entry_points_mock):
        mock_entry_point = mock.Mock()
        mock_entry_point.load.return_value = DummyExtension

        iter_entry_points_mock.return_value = [mock_entry_point]

        with mock.patch.object(DummyExtension, 'get_command') as get:
            get.side_effect = Exception

            assert ext.load_extensions() == []
            get.assert_called_once_with()


class TestValidateExtensionData(object):

    @pytest.fixture
    def ext_data(self):
        extension = DummyExtension()

        entry_point = mock.Mock()
        entry_point.name = extension.ext_name

        schema = extension.get_config_schema()
        defaults = extension.get_default_config()
        command = extension.get_command()

        return ext.ExtensionData(
            extension, entry_point, schema, defaults, command)

    def test_name_mismatch(self, ext_data):
        ext_data.entry_point.name = 'barfoo'
        assert not ext.validate_extension_data(ext_data)

    def test_distribution_not_found(self, ext_data):
        error = pkg_resources.DistributionNotFound
        ext_data.entry_point.require.side_effect = error
        assert not ext.validate_extension_data(ext_data)

    def test_version_conflict(self, ext_data):
        error = pkg_resources.VersionConflict
        ext_data.entry_point.require.side_effect = error
        assert not ext.validate_extension_data(ext_data)

    def test_entry_point_require_exception(self, ext_data):
        ext_data.entry_point.require.side_effect = Exception

        # Hope that entry points are well behaved, so exception will bubble.
        with pytest.raises(Exception):
            assert not ext.validate_extension_data(ext_data)

    def test_extenions_validate_environment_error(self, ext_data):
        extension = ext_data.extension
        with mock.patch.object(extension, 'validate_environment') as validate:
            validate.side_effect = exceptions.ExtensionError('error')

            assert not ext.validate_extension_data(ext_data)
            validate.assert_called_once_with()

    def test_extenions_validate_environment_exception(self, ext_data):
        extension = ext_data.extension
        with mock.patch.object(extension, 'validate_environment') as validate:
            validate.side_effect = Exception

            assert not ext.validate_extension_data(ext_data)
            validate.assert_called_once_with()

    def test_missing_schema(self, ext_data):
        ext_data = ext_data._replace(config_schema=None)
        assert not ext.validate_extension_data(ext_data)

    def test_schema_that_is_missing_enabled(self, ext_data):
        del ext_data.config_schema['enabled']
        ext_data.config_schema['baz'] = config.String()
        assert not ext.validate_extension_data(ext_data)

    def test_schema_with_wrong_types(self, ext_data):
        ext_data.config_schema['enabled'] = 123
        assert not ext.validate_extension_data(ext_data)

    def test_schema_with_invalid_type(self, ext_data):
        ext_data.config_schema['baz'] = 123
        assert not ext.validate_extension_data(ext_data)

    def test_no_default_config(self, ext_data):
        ext_data = ext_data._replace(config_defaults=None)
        assert not ext.validate_extension_data(ext_data)

    def test_get_cache_dir(self, ext_data):
        core_cache_dir = '/tmp'
        config = {'core': {'cache_dir': core_cache_dir}}
        extension = ext_data.extension

        with mock.patch.object(ext.path, 'get_or_create_dir'):
            cache_dir = extension.get_cache_dir(config)

        expected = os.path.join(core_cache_dir, extension.ext_name)
        assert cache_dir == expected

    def test_get_config_dir(self, ext_data):
        core_config_dir = '/tmp'
        config = {'core': {'config_dir': core_config_dir}}
        extension = ext_data.extension

        with mock.patch.object(ext.path, 'get_or_create_dir'):
            config_dir = extension.get_config_dir(config)

        expected = os.path.join(core_config_dir, extension.ext_name)
        assert config_dir == expected

    def test_get_data_dir(self, ext_data):
        core_data_dir = '/tmp'
        config = {'core': {'data_dir': core_data_dir}}
        extension = ext_data.extension

        with mock.patch.object(ext.path, 'get_or_create_dir'):
            data_dir = extension.get_data_dir(config)

        expected = os.path.join(core_data_dir, extension.ext_name)
        assert data_dir == expected
