from __future__ import absolute_import, unicode_literals

import mock

import pkg_resources

import pytest

from mopidy import config, exceptions, ext

from tests import IsA, any_unicode


class TestExtension(ext.Extension):
    dist_name = 'Mopidy-Foobar'
    ext_name = 'foobar'
    version = '1.2.3'

    def get_default_config(self):
        return '[foobar]\nenabled = true'


any_testextension = IsA(TestExtension)


# ext.Extension

@pytest.fixture
def extension():
    return ext.Extension()


def test_dist_name_is_none(extension):
    assert extension.dist_name is None


def test_ext_name_is_none(extension):
    assert extension.ext_name is None


def test_version_is_none(extension):
    assert extension.version is None


def test_get_default_config_raises_not_implemented(extension):
    with pytest.raises(NotImplementedError):
        extension.get_default_config()


def test_get_config_schema_returns_extension_schema(extension):
    schema = extension.get_config_schema()
    assert isinstance(schema['enabled'], config.Boolean)


def test_validate_environment_does_nothing_by_default(extension):
    assert extension.validate_environment() is None


def test_setup_raises_not_implemented(extension):
    with pytest.raises(NotImplementedError):
        extension.setup(None)


# ext.load_extensions

@pytest.fixture
def iter_entry_points_mock(request):
    patcher = mock.patch('pkg_resources.iter_entry_points')
    iter_entry_points = patcher.start()
    iter_entry_points.return_value = []
    request.addfinalizer(patcher.stop)
    return iter_entry_points


def test_load_extensions_no_extenions(iter_entry_points_mock):
    iter_entry_points_mock.return_value = []
    assert [] == ext.load_extensions()


def test_load_extensions(iter_entry_points_mock):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension

    iter_entry_points_mock.return_value = [mock_entry_point]

    expected = ext.ExtensionData(
        any_testextension, mock_entry_point, IsA(config.ConfigSchema),
        any_unicode, None)

    assert ext.load_extensions() == [expected]


def test_load_extensions_gets_wrong_class(iter_entry_points_mock):

    class WrongClass(object):
        pass

    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = WrongClass

    iter_entry_points_mock.return_value = [mock_entry_point]

    assert [] == ext.load_extensions()


def test_load_extensions_gets_instance(iter_entry_points_mock):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension()

    iter_entry_points_mock.return_value = [mock_entry_point]

    assert [] == ext.load_extensions()


def test_load_extensions_creating_instance_fails(iter_entry_points_mock):
    mock_extension = mock.Mock(spec=ext.Extension)
    mock_extension.side_effect = Exception

    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = mock_extension

    iter_entry_points_mock.return_value = [mock_entry_point]

    assert [] == ext.load_extensions()


def test_load_extensions_get_config_schema_fails(iter_entry_points_mock):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension

    iter_entry_points_mock.return_value = [mock_entry_point]

    with mock.patch.object(TestExtension, 'get_config_schema') as get_schema:
        get_schema.side_effect = Exception
        assert [] == ext.load_extensions()
        get_schema.assert_called_once_with()


def test_load_extensions_get_default_config_fails(iter_entry_points_mock):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension

    iter_entry_points_mock.return_value = [mock_entry_point]

    with mock.patch.object(TestExtension, 'get_default_config') as get_default:
        get_default.side_effect = Exception
        assert [] == ext.load_extensions()
        get_default.assert_called_once_with()


def test_load_extensions_get_command_fails(iter_entry_points_mock):
    mock_entry_point = mock.Mock()
    mock_entry_point.load.return_value = TestExtension

    iter_entry_points_mock.return_value = [mock_entry_point]

    with mock.patch.object(TestExtension, 'get_command') as get_command:
        get_command.side_effect = Exception
        assert [] == ext.load_extensions()
        get_command.assert_called_once_with()


# ext.validate_extension_data

@pytest.fixture
def ext_data():
    extension = TestExtension()

    entry_point = mock.Mock()
    entry_point.name = extension.ext_name

    schema = extension.get_config_schema()
    defaults = extension.get_default_config()
    command = extension.get_command()

    return ext.ExtensionData(extension, entry_point, schema, defaults, command)


def test_validate_extension_name_mismatch(ext_data):
    ext_data.entry_point.name = 'barfoo'
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_distribution_not_found(ext_data):
    error = pkg_resources.DistributionNotFound
    ext_data.entry_point.require.side_effect = error
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_version_conflict(ext_data):
    ext_data.entry_point.require.side_effect = pkg_resources.VersionConflict
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_exception(ext_data):
    ext_data.entry_point.require.side_effect = Exception

    # We trust that entry points are well behaved, so exception will bubble.
    with pytest.raises(Exception):
        assert not ext.validate_extension_data(ext_data)


def test_validate_extension_instance_validate_env_ext_error(ext_data):
    extension = ext_data.extension
    with mock.patch.object(extension, 'validate_environment') as validate:
        validate.side_effect = exceptions.ExtensionError('error')

        assert not ext.validate_extension_data(ext_data)
        validate.assert_called_once_with()


def test_validate_extension_instance_validate_env_exception(ext_data):
    extension = ext_data.extension
    with mock.patch.object(extension, 'validate_environment') as validate:
        validate.side_effect = Exception

        assert not ext.validate_extension_data(ext_data)
        validate.assert_called_once_with()


def test_validate_extension_with_missing_schema(ext_data):
    ext_data = ext_data._replace(config_schema=None)
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_with_schema_that_is_missing_enabled(ext_data):
    del ext_data.config_schema['enabled']
    ext_data.config_schema['baz'] = config.String()
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_with_schema_with_wrong_types(ext_data):
    ext_data.config_schema['enabled'] = 123
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_with_schema_with_invalid_type(ext_data):
    ext_data.config_schema['baz'] = 123
    assert not ext.validate_extension_data(ext_data)


def test_validate_extension_with_no_defaults(ext_data):
    ext_data = ext_data._replace(config_defaults=None)
    assert not ext.validate_extension_data(ext_data)
